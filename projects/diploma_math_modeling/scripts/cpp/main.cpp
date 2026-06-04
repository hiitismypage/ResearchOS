#include "model.hpp"
#include "simulate.cpp"

#include <fstream>
#include <sstream>
#include <iostream>
#include <string>
#include <unordered_map>

static std::vector<std::vector<std::string>>
read_csv(const std::string& path)
{
    std::ifstream f(path);
    std::vector<std::vector<std::string>> rows;
    std::string line;
    while (std::getline(f, line)) {
        std::vector<std::string> row;
        std::stringstream ss(line);
        std::string cell;
        while (std::getline(ss, cell, ','))
            row.push_back(cell);
        rows.push_back(row);
    }
    return rows;
}

static double to_d(const std::string& s)
{
    try { return std::stod(s); }
    catch (...) { return 0.0; }
}

static Model load_model(const std::string& cal_dir)
{
    Model m;

    auto sp_rows = read_csv(cal_dir + "/csv/sector_params.csv");
    std::vector<std::string> col_names = sp_rows[0];
    auto col_idx = [&](const std::string& name) -> int {
        for (int i = 0; i < (int)col_names.size(); ++i)
            if (col_names[i] == name) return i;
        return -1;
    };

    int ci_delta = col_idx("delta"), ci_nu    = col_idx("nu");
    int ci_kappa = col_idx("kappa"), ci_eta   = col_idx("eta");
    int ci_alpha = col_idx("alpha"), ci_p_inn = col_idx("p_inn");
    int ci_mu    = col_idx("mu");

    for (int j = 0; j < N; ++j) {
        auto& row = sp_rows[j + 1];
        m.params[j] = {
            to_d(row[ci_delta]), to_d(row[ci_nu]),
            to_d(row[ci_kappa]), to_d(row[ci_eta]),
            to_d(row[ci_alpha]), to_d(row[ci_p_inn]),
            to_d(row[ci_mu])
        };
    }

    auto load_mat = [&](const std::string& name) -> Mat5 {
        auto rows = read_csv(cal_dir + "/csv/" + name + ".csv");
        Mat5 M = Mat5::Zero();
        for (int i = 0; i < N; ++i)
            for (int j = 0; j < N; ++j)
                M(i, j) = to_d(rows[i + 1][j + 1]);
        return M;
    };

    m.A  = load_mat("A0");
    m.B  = load_mat("B0");
    m.B0 = m.B;

    auto ux_rows = read_csv(cal_dir + "/csv/u0_X0.csv");
    for (int j = 0; j < N; ++j) {
        m.u(j) = to_d(ux_rows[j + 1][1]);
        m.x(j) = to_d(ux_rows[j + 1][2]);
    }

    Vec5 u_leontief = (Mat5::Identity() - m.A) * m.x;
    for (int j = 0; j < N; ++j)
        m.u(j) = std::max(u_leontief(j), 1e-2);

    const std::array<std::string, N> snames = {
        "extraction", "energy", "manufacturing", "construction", "agriculture"
    };
    for (int j = 0; j < N; ++j) {
        auto rows = read_csv(cal_dir + "/csv/firms_" + snames[j] + ".csv");
        int Nj = (int)rows.size() - 1;
        m.n_firms[j] = Nj;

        FirmBlock& fb = m.firms[j];
        fb.k.resize(Nj);
        fb.theta.resize(Nj);
        fb.omega.resize(Nj);
        fb.d_e.resize(Nj);
        fb.c_f.resize(Nj);
        fb.a_f.resize(N, Nj);
        fb.gamma_f.resize(N, Nj);

        auto hdr = rows[0];
        auto ci = [&](const std::string& name) -> int {
            for (int i = 0; i < (int)hdr.size(); ++i)
                if (hdr[i] == name) return i;
            return -1;
        };

        for (int f = 0; f < Nj; ++f) {
            auto& r = rows[f + 1];
            fb.k(f)     = to_d(r[ci("k0")]);
            fb.theta(f) = to_d(r[ci("theta0")]);
            fb.omega(f) = to_d(r[ci("omega0")]);
            fb.c_f(f)   = to_d(r[ci("c_f")]);
            fb.d_e(f)   = fb.omega(f) * m.x(j);
        }

        const std::array<std::string, N> snames_cap = {
            "Extraction", "Energy", "Manufacturing", "Construction", "Agriculture"
        };
        for (int i = 0; i < N; ++i) {
            int ci_a = ci("a_" + snames_cap[i]);
            int ci_g = ci("gamma_" + snames_cap[i]);
            for (int f = 0; f < Nj; ++f) {
                auto& r = rows[f + 1];
                if (ci_a >= 0) fb.a_f(i, f)     = to_d(r[ci_a]);
                if (ci_g >= 0) fb.gamma_f(i, f)  = to_d(r[ci_g]);
            }
        }
    }

    return m;
}

int main(int argc, char* argv[])
{
    std::string cal_dir = (argc > 1) ? argv[1] : "results/calibration";
    std::string out_dir = (argc > 2) ? argv[2] : "results/simulation_cpp";
    uint64_t    seed    = (argc > 3) ? std::stoull(argv[3]) : 42ULL;

    std::cout << "Loading calibration from: " << cal_dir << "\n";
    Model m = load_model(cal_dir);
    std::cout << "Sectors: " << N
              << "  Total firms: ";
    int total = 0;
    for (int j = 0; j < N; ++j) total += m.n_firms[j];
    std::cout << total << "\n";

    std::cout << "Running simulation (T=" << T_STEPS
              << ", G_U=" << G_U << ")...\n";
    auto traj = run(m, seed);

    const std::array<std::string, N> snames = {
        "Extraction", "Energy", "Manufacturing", "Construction", "Agriculture"
    };

    std::string csv_path = out_dir + "/macro_trajectory.csv";
    save_trajectory(traj, csv_path, snames);
    std::cout << "Saved: " << csv_path << "  (" << traj.size() << " rows)\n";

    const auto& t0  = traj.front();
    const auto& tT  = traj.back();
    std::cout << "\nGDP 2015: " << t0.gdp / 1e6 << " trl EUR"
              << "  →  2045: " << tT.gdp / 1e6 << " trl EUR\n";
    std::cout << "rho_A:    " << t0.rho_A << "  →  " << tT.rho_A << "\n";

    return 0;
}
