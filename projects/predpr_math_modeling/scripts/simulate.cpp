#include <Eigen/Dense>
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>
#include <vector>

namespace fs = std::filesystem;

static constexpr int    N             = 5;
static constexpr int    T             = 30;
static constexpr int    BASE_YEAR     = 2015;
static constexpr double G_U           = 0.015;
static constexpr double EPS_B         = 1.0;
static constexpr double FC_RATE       = 0.02;
static constexpr double SIGMA_K       = 0.6;
static constexpr double SIGMA_A       = 0.15;
static constexpr double CLIP_B_FACTOR = 5.0;
static constexpr double CLIP_B_ABS    = 1.0;

static const std::array<int, N> N_FIRMS = {32, 27, 41, 25, 34};

static const std::array<std::string, N> SECTOR_NAMES = {
    "Dobyvayushchaya", "Energetika", "Obrabatyvayushchaya", "Stroitelstvo", "Selskoe_khoz"
};

using Mat5  = Eigen::Matrix<double, N, N>;
using Vec5  = Eigen::Matrix<double, N, 1>;
using MatXX = Eigen::MatrixXd;
using VecX  = Eigen::VectorXd;

static Vec5 make_X0() {
    Vec5 v;
    v << 10746.0, 106178.0, 1675563.0, 297148.0, 50958.0;
    return v;
}

static Mat5 make_A0() {
    Mat5 A;
    A << 0.0578, 0.1214, 0.0268, 0.0068, 0.0020,
         0.0276, 0.2281, 0.0133, 0.0022, 0.0158,
         0.2136, 0.0735, 0.3980, 0.2336, 0.1901,
         0.0218, 0.0323, 0.0052, 0.0769, 0.0168,
         0.0042, 0.0001, 0.0255, 0.0000, 0.0675;
    return A;
}

static Mat5 make_B0() {
    Mat5 B;
    B << 0.0008, 0.0017, 0.0014, 0.0006, 0.0010,
         0.0000, 0.0000, 0.0000, 0.0000, 0.0000,
         2.4017, 5.2517, 4.2448, 1.9640, 2.9229,
         2.0997, 4.5914, 3.7110, 1.7171, 2.5554,
         0.0041, 0.0090, 0.0072, 0.0033, 0.0050;
    return B;
}

static Vec5 make_U0(const Mat5& A0, const Vec5& X0) {
    return ((Mat5::Identity() - A0) * X0).cwiseMax(0.01);
}

static const std::array<double, N> DELTA = {0.060, 0.040, 0.055, 0.065, 0.050};
static const std::array<double, N> NU    = {0.140, 0.165, 0.189, 0.134, 0.145};
static const std::array<double, N> KAPPA = {0.125, 0.050, 0.450, 0.180, 0.050};
static const std::array<double, N> ETA   = {0.010, 0.010, 0.012, 0.015, 0.010};
static const std::array<double, N> ALPHA = {0.300, 0.300, 0.300, 0.513, 0.300};
static const std::array<double, N> P_INN = {0.158, 0.183, 0.050, 0.050, 0.183};
static const std::array<double, N> MU    = {0.027, 0.024, 0.022, 0.027, 0.026};

static const std::array<double, N> K_J      = {78100.0, 707000.0, 8885500.0, 2252700.0, 368200.0};
static const std::array<double, N> THETA_LO = {0.7, 0.7, 0.5, 0.6, 0.5};
static const std::array<double, N> THETA_HI = {1.3, 1.3, 1.5, 1.4, 1.5};

struct SectorFirms {
    int Nj;
    std::vector<double> k, theta, omega, c_f, d_e;
    MatXX a_f, gamma_f;
};

using AllFirms = std::array<SectorFirms, N>;

static Vec5 leontief_target(const Vec5&, const Mat5& A, const Mat5& B, const Vec5& u) {
    return (Mat5::Identity() - A - G_U * B).lu().solve(u).cwiseMax(0.0);
}

static double hhi(const std::vector<double>& omega) {
    double s = 0.0;
    for (double w : omega) s += w * w;
    return s;
}

static double io_balance_residual(const Vec5& x, const Vec5& xn,
                                  const Mat5& An, const Mat5& Bn, const Vec5& u) {
    Vec5 r = xn - An * xn - Bn * (xn - x) - u;
    return r.norm() / (xn.norm() + 1e-15);
}

static AllFirms init_firms(const Mat5& A0, const Mat5& B0,
                           const Vec5& X0, std::mt19937_64& rng) {
    AllFirms firms;
    for (int j = 0; j < N; ++j) {
        int Nj = N_FIRMS[j]; double Kj = K_J[j];
        SectorFirms& sf = firms[j];
        sf.Nj = Nj;
        sf.k.resize(Nj); sf.theta.resize(Nj); sf.omega.resize(Nj);
        sf.c_f.resize(Nj); sf.d_e.resize(Nj);
        sf.a_f.resize(N, Nj); sf.gamma_f.resize(N, Nj);

        double mu_k = std::log(std::max(Kj / Nj, 1e-15)) - 0.5 * SIGMA_K * SIGMA_K;
        std::lognormal_distribution<double> lnd(mu_k, SIGMA_K);
        double k_sum = 0.0;
        for (int f = 0; f < Nj; ++f) { sf.k[f] = lnd(rng); k_sum += sf.k[f]; }
        for (int f = 0; f < Nj; ++f) sf.k[f] *= Kj / k_sum;

        std::uniform_real_distribution<double> uid(THETA_LO[j], THETA_HI[j]);
        for (int f = 0; f < Nj; ++f) sf.theta[f] = uid(rng);

        double ksum2 = 0.0;
        for (double v : sf.k) ksum2 += v;
        for (int f = 0; f < Nj; ++f) sf.omega[f] = sf.k[f] / ksum2;

        std::normal_distribution<double> nd(0.0, 1.0);
        for (int i = 0; i < N; ++i) {
            VecX raw(Nj);
            for (int f = 0; f < Nj; ++f)
                raw[f] = A0(i, j) * std::exp(SIGMA_A * nd(rng));
            double agg = 0.0;
            for (int f = 0; f < Nj; ++f) agg += sf.omega[f] * raw[f];
            double scale = (agg > 1e-300 && A0(i, j) > 0) ? A0(i, j) / agg : 1.0;
            for (int f = 0; f < Nj; ++f) sf.a_f(i, f) = raw[f] * scale;
        }

        double theta_mid = 0.5 * (THETA_LO[j] + THETA_HI[j]);
        for (int f = 0; f < Nj; ++f)
            sf.c_f[f] = FC_RATE * NU[j] * theta_mid * sf.k[f];

        VecX weights = B0.col(j).cwiseMax(0.0);
        double w_sum = weights.sum();
        VecX gamma_j(N);
        if (w_sum > 0) {
            gamma_j = weights / w_sum;
        } else {
            VecX a_col = A0.col(j).cwiseMax(0.0);
            double as  = a_col.sum();
            gamma_j = (as > 0) ? (a_col / as) : VecX::Constant(N, 1.0 / N);
        }
        for (int f = 0; f < Nj; ++f) sf.gamma_f.col(f) = gamma_j;
        for (int f = 0; f < Nj; ++f) sf.d_e[f] = sf.omega[f] * X0[j];
    }
    return firms;
}

struct StepResult { Vec5 x_new, I_agg; Mat5 A_new, B_new; AllFirms firms_new; };

static StepResult step(const Vec5& x, const Mat5& A, const Mat5& B,
                       const Vec5& u, const AllFirms& firms,
                       const Mat5& B0_ref, std::mt19937_64& rng) {
    StepResult res;
    res.firms_new = firms;
    Vec5 x_star = leontief_target(x, A, B, u);

    std::array<std::vector<double>, N> x_jf_arr;
    std::array<MatXX, N> z_ijf_arr, q_ijf_arr;
    Vec5 I_agg = Vec5::Zero();

    for (int j = 0; j < N; ++j) {
        const SectorFirms& sf  = firms[j];
        SectorFirms&       sfn = res.firms_new[j];
        int Nj = sf.Nj;
        x_jf_arr[j].resize(Nj);
        z_ijf_arr[j].resize(N, Nj);
        q_ijf_arr[j].resize(N, Nj);

        std::vector<double> d_jf(Nj), d_e_new(Nj), x_bar(Nj),
                            x_jf(Nj), pi_jf(Nj), I_exp(Nj), I_tot(Nj);

        for (int f = 0; f < Nj; ++f) {
            d_jf[f]    = sf.omega[f] * x_star[j];
            d_e_new[f] = ALPHA[j] * sf.d_e[f] + (1.0 - ALPHA[j]) * d_jf[f];
            x_bar[f]   = NU[j] * sf.theta[f] * sf.k[f];
            x_jf[f]    = std::max(0.0, std::min({d_e_new[f], d_jf[f], x_bar[f]}));
            x_jf_arr[j][f] = x_jf[f];

            double z_sum = 0.0;
            for (int i = 0; i < N; ++i) {
                z_ijf_arr[j](i, f) = sf.a_f(i, f) * x_jf[f];
                z_sum += sf.a_f(i, f) * x_jf[f];
            }
            pi_jf[f] = x_jf[f] - z_sum - sf.c_f[f];

            double cap_gap = std::max(0.0, d_jf[f] - x_bar[f]);
            I_exp[f] = KAPPA[j] * std::max(0.0, pi_jf[f]) + ETA[j] * cap_gap;
            I_tot[f] = DELTA[j] * sf.k[f] + I_exp[f];

            for (int i = 0; i < N; ++i)
                q_ijf_arr[j](i, f) = sf.gamma_f(i, f) * I_exp[f];

            sfn.k[f]     = std::max(0.0, (1.0 - DELTA[j]) * sf.k[f] + I_tot[f]);
            sfn.theta[f] = sf.theta[f] * (1.0 + MU[j] * I_tot[f] / std::max(sf.k[f], 1.0));

            std::bernoulli_distribution bern(P_INN[j]);
            if (bern(rng)) {
                std::uniform_real_distribution<double> ud(0.0, MU[j]);
                double reduc = ud(rng);
                for (int i = 0; i < N; ++i)
                    sfn.a_f(i, f) = std::max(0.0, sf.a_f(i, f) * (1.0 - reduc));
            } else {
                for (int i = 0; i < N; ++i) sfn.a_f(i, f) = sf.a_f(i, f);
            }
            sfn.d_e[f] = d_e_new[f];
        }

        double x_tot = 0.0;
        for (double v : x_jf) x_tot += v;
        if (x_tot > 1e-9)
            for (int f = 0; f < Nj; ++f) sfn.omega[f] = x_jf[f] / x_tot;
        else
            sfn.omega = sf.omega;

        double I_j = 0.0;
        for (int f = 0; f < Nj; ++f) I_j += I_exp[f];
        I_agg[j] = I_j;
    }

    for (int j = 0; j < N; ++j) {
        double s = 0.0;
        for (double v : x_jf_arr[j]) s += v;
        res.x_new[j] = s;
    }

    res.A_new = A;
    for (int j = 0; j < N; ++j) {
        double xs = 0.0;
        for (double v : x_jf_arr[j]) xs += v;
        if (xs > 1e-9)
            for (int i = 0; i < N; ++i) {
                double zs = 0.0;
                for (int f = 0; f < firms[j].Nj; ++f) zs += z_ijf_arr[j](i, f);
                res.A_new(i, j) = zs / xs;
            }
    }

    res.B_new = Mat5::Zero();
    for (int j = 0; j < N; ++j) {
        double dX = std::max(std::abs(res.x_new[j] - x[j]), EPS_B);
        for (int i = 0; i < N; ++i) {
            double qs = 0.0;
            for (int f = 0; f < firms[j].Nj; ++f) qs += q_ijf_arr[j](i, f);
            double ceil = (B0_ref(i, j) > 0) ? CLIP_B_FACTOR * B0_ref(i, j) : CLIP_B_ABS;
            res.B_new(i, j) = std::clamp(qs / dX, 0.0, ceil);
        }
    }

    res.I_agg = I_agg;
    return res;
}

struct SimRow {
    int t, year;
    double rho_A, GDP_proxy, K_total, U_total, balance_resid, I_total;
    std::array<double, N> X_j, K_j, theta_j, HHI_j, I_j;
};

static void write_csv(const std::vector<SimRow>& rows, const std::string& path) {
    std::ofstream f(path);
    f << "t,year,rho_A,GDP_proxy,K_total,U_total,balance_resid,I_total";
    for (int j = 0; j < N; ++j) f << ",X_" << SECTOR_NAMES[j];
    for (int j = 0; j < N; ++j) f << ",K_" << SECTOR_NAMES[j];
    for (int j = 0; j < N; ++j) f << ",theta_" << SECTOR_NAMES[j];
    for (int j = 0; j < N; ++j) f << ",HHI_" << SECTOR_NAMES[j];
    for (int j = 0; j < N; ++j) f << ",I_" << SECTOR_NAMES[j];
    f << "\n" << std::fixed << std::setprecision(6);
    for (const auto& r : rows) {
        f << r.t << "," << r.year << ","
          << r.rho_A << "," << r.GDP_proxy << "," << r.K_total << ","
          << r.U_total << "," << r.balance_resid << "," << r.I_total;
        for (int j = 0; j < N; ++j) f << "," << r.X_j[j];
        for (int j = 0; j < N; ++j) f << "," << r.K_j[j];
        for (int j = 0; j < N; ++j) f << "," << r.theta_j[j];
        for (int j = 0; j < N; ++j) f << "," << r.HHI_j[j];
        for (int j = 0; j < N; ++j) f << "," << r.I_j[j];
        f << "\n";
    }
}

static std::vector<SimRow> run_simulation(uint64_t seed = 42) {
    std::mt19937_64 rng(seed);
    Mat5 A0 = make_A0(), A = A0;
    Mat5 B0 = make_B0(), B = B0;
    Vec5 X0 = make_X0(), x = X0;
    Vec5 u  = make_U0(A0, X0);
    AllFirms firms = init_firms(A0, B0, X0, rng);

    std::vector<SimRow> rows;
    rows.reserve(T + 1);

    for (int t = 0; t <= T; ++t) {
        SimRow row{};
        row.t    = t;
        row.year = BASE_YEAR + t;

        Eigen::EigenSolver<Mat5> es(A, false);
        row.rho_A = es.eigenvalues().cwiseAbs().maxCoeff();

        double K_tot = 0.0;
        for (int j = 0; j < N; ++j) {
            row.X_j[j] = x[j];
            double Kj = 0.0;
            for (double v : firms[j].k) Kj += v;
            row.K_j[j] = Kj; K_tot += Kj;
            double th = 0.0;
            for (double v : firms[j].theta) th += v;
            row.theta_j[j] = th / firms[j].Nj;
            row.HHI_j[j]   = hhi(firms[j].omega);
        }
        row.GDP_proxy     = x.sum();
        row.K_total       = K_tot;
        row.U_total       = u.sum();
        row.balance_resid = 0.0;
        row.I_total       = 0.0;
        for (int j = 0; j < N; ++j) row.I_j[j] = 0.0;

        rows.push_back(row);
        if (t == T) break;

        StepResult sr = step(x, A, B, u, firms, B0, rng);
        rows.back().balance_resid = io_balance_residual(x, sr.x_new, sr.A_new, sr.B_new, u);
        rows.back().I_total = sr.I_agg.sum();
        for (int j = 0; j < N; ++j) rows.back().I_j[j] = sr.I_agg[j];

        u *= (1.0 + G_U);
        x = sr.x_new; A = sr.A_new; B = sr.B_new; firms = sr.firms_new;
    }
    return rows;
}

static void print_summary(const std::vector<SimRow>& rows) {
    const int steps[] = {0, 5, 10, 20, 30};
    std::cout << "\n" << std::string(80, '=') << "\n";
    std::cout << "Sector output X_j(t), M EUR\n" << std::string(80, '-') << "\n";
    std::cout << std::setw(4) << "t" << std::setw(7) << "Year";
    for (const auto& s : SECTOR_NAMES) std::cout << std::setw(14) << s.substr(0, 10);
    std::cout << "\n" << std::string(80, '-') << "\n";
    for (int tw : steps)
        for (const auto& r : rows) {
            if (r.t != tw) continue;
            std::cout << std::setw(4) << r.t << std::setw(7) << r.year;
            for (int j = 0; j < N; ++j)
                std::cout << std::fixed << std::setprecision(0) << std::setw(14) << r.X_j[j];
            std::cout << "\n"; break;
        }

    std::cout << "\n" << std::string(80, '-') << "\n";
    std::cout << "System indicators\n" << std::string(80, '-') << "\n";
    std::cout << std::setw(4) << "t" << std::setw(7) << "Year"
              << std::setw(9) << "rho_A" << std::setw(11) << "GDP_idx%"
              << std::setw(12) << "balance\n" << std::string(80, '-') << "\n";
    double gdp0 = rows[0].GDP_proxy;
    for (int tw : steps)
        for (const auto& r : rows) {
            if (r.t != tw) continue;
            std::cout << std::setw(4) << r.t << std::setw(7) << r.year
                      << std::setw(9)  << std::fixed << std::setprecision(4) << r.rho_A
                      << std::setw(10) << std::setprecision(2)
                                       << r.GDP_proxy / gdp0 * 100.0 << "%"
                      << std::setw(14) << std::scientific << std::setprecision(3)
                                       << r.balance_resid << "\n";
            break;
        }
    std::cout << std::string(80, '=') << "\n\n";
}

int main(int argc, char* argv[]) {
    std::string out_dir = "simulation_output";
    uint64_t    seed    = 42;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--seed" && i + 1 < argc)
            seed = static_cast<uint64_t>(std::stoll(argv[++i]));
        else if (arg.rfind("--", 0) != 0)
            out_dir = arg;
    }
    fs::create_directories(out_dir);

    std::cout << std::string(65, '=') << "\n";
    std::cout << "Two-level ABM IOB -- forward simulation\n";
    std::cout << "Five-sector economy, base year " << BASE_YEAR << ", T=" << T << "\n";
    int total = 0; for (int v : N_FIRMS) total += v;
    std::cout << "Sectors: " << N << " | Agents: " << total
              << " | G_U=" << G_U << " | seed=" << seed << "\n";
    std::cout << std::string(65, '=') << "\n";

    auto t0 = std::chrono::steady_clock::now();
    std::cout << "[1/2] Running simulation...\n";
    std::vector<SimRow> rows = run_simulation(seed);
    double elapsed = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - t0).count();
    std::cout << "      Done in " << std::fixed << std::setprecision(2) << elapsed << " s\n";

    print_summary(rows);

    std::string csv_path = out_dir + "/macro_trajectory.csv";
    write_csv(rows, csv_path);
    std::cout << "[2/2] Results saved -> " << csv_path << "\n";
    std::cout << std::string(65, '=') << "\n";
    return 0;
}
