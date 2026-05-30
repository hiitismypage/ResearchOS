#include <Eigen/Dense>
#include <Eigen/SVD>
#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;

static constexpr int N = 5;
using Mat5 = Eigen::Matrix<double, N, N>;
using Vec5 = Eigen::Matrix<double, N, 1>;

const std::array<std::string, N> SECTOR_NAMES = {
    "Extraction", "Energy", "Manufacturing", "Construction", "Agriculture"
};

static Eigen::MatrixXd read_csv_matrix(const std::string& path, int rows, int cols) {
    std::ifstream f(path);
    if (!f.is_open()) throw std::runtime_error("Cannot open: " + path);
    Eigen::MatrixXd M(rows, cols);
    std::string line, tok;
    std::getline(f, line);
    for (int i = 0; i < rows; ++i) {
        if (!std::getline(f, line)) throw std::runtime_error("Too few rows: " + path);
        for (char& c : line) if (c == ';') c = ',';
        std::stringstream ss(line);
        std::getline(ss, tok, ',');
        for (int j = 0; j < cols; ++j) {
            if (!std::getline(ss, tok, ',')) throw std::runtime_error("Too few cols: " + path);
            M(i, j) = std::stod(tok);
        }
    }
    return M;
}

static Vec5 read_csv_vector(const std::string& path) {
    return read_csv_matrix(path, N, 1).col(0);
}

static Mat5 compute_A(const Mat5& Z, const Vec5& X) {
    Mat5 A;
    for (int j = 0; j < N; ++j) {
        double xj = X[j] > 0 ? X[j] : 1.0;
        for (int i = 0; i < N; ++i) A(i, j) = Z(i, j) / xj;
    }
    return A;
}

static void compute_B(const Mat5& Q, const Vec5& dX, double eps_b,
                      Mat5& B_out, Mat5& B_plus_out) {
    for (int j = 0; j < N; ++j) {
        double dxj = std::max(std::abs(dX[j]), eps_b);
        for (int i = 0; i < N; ++i) B_out(i, j) = Q(i, j) / dxj;
    }
    Eigen::JacobiSVD<Mat5> svd(B_out, Eigen::ComputeFullU | Eigen::ComputeFullV);
    Vec5 s = svd.singularValues(), sp;
    double tol = 1e-10 * s.maxCoeff();
    for (int i = 0; i < N; ++i) sp[i] = s[i] > tol ? 1.0 / s[i] : 0.0;
    B_plus_out = svd.matrixV() * sp.asDiagonal() * svd.matrixU().transpose();
}

static Mat5 build_Q(const Vec5& gfcf, const Vec5& X) {
    double xt = X.sum();
    Vec5 w = xt > 0 ? Vec5(X / xt) : Vec5::Constant(1.0 / N);
    return gfcf * w.transpose();
}

struct SectorBehavioral { Vec5 delta, nu, kappa, eta, alpha, p_inn, mu; };

static SectorBehavioral calibrate_behavioral(
    const Vec5& GVA, const Vec5& D1, const Vec5& GFCF,
    const Vec5& X_avg, const Vec5& vol,
    double K_total, double Am, const Vec5& dm)
{
    SectorBehavioral p;
    for (int j = 0; j < N; ++j) p.delta[j] = Am * dm[j];

    double gvat = GVA.sum();
    Vec5 Kj = gvat > 0 ? Vec5(GVA / gvat * K_total) : Vec5::Constant(K_total / N);
    for (int j = 0; j < N; ++j) p.nu[j] = X_avg[j] / std::max(Kj[j], 1.0);

    Vec5 pi = GVA - D1;
    double epi = 1e-3 * std::max(X_avg.sum() / N, 1.0);
    for (int j = 0; j < N; ++j)
        p.kappa[j] = std::clamp(GFCF[j] / std::max(pi[j], epi), 0.05, 0.45);

    for (int j = 0; j < N; ++j)
        p.eta[j] = std::clamp(0.10 * GFCF[j] / std::max(X_avg[j], 1.0), 0.01, 0.25);

    double mv = vol.mean();
    for (int j = 0; j < N; ++j)
        p.alpha[j] = std::clamp(1.0 - (mv > 1e-6 ? vol[j] / mv : 1.0), 0.30, 0.90);

    double kmax = p.kappa.maxCoeff(); if (kmax < 1e-9) kmax = 1.0;
    for (int j = 0; j < N; ++j) p.p_inn[j] = 0.05 + 0.15 * (1.0 - p.kappa[j] / kmax);

    for (int j = 0; j < N; ++j)
        p.mu[j] = std::clamp(0.01 + 0.04 * GVA[j] / std::max(X_avg[j], 1.0), 0.01, 0.05);

    return p;
}

static void validate(const Mat5& A, const Mat5& B, const Mat5& Bp, const Vec5& X, const Vec5& u) {
    Eigen::EigenSolver<Mat5> es(A, false);
    double rho = es.eigenvalues().cwiseAbs().maxCoeff();
    std::cout << "rho(A0) = " << std::fixed << std::setprecision(6) << rho
              << (rho < 1.0 ? " [OK]\n" : " [WARN: rho >= 1]\n");

    double rel = (X - (A * X + u)).norm() / std::max(X.norm(), 1e-12);
    std::cout << "Static balance residual = " << std::scientific << rel << "\n";

    Eigen::JacobiSVD<Mat5> svd(B);
    int rk = (int)(svd.singularValues().array() > 1e-10 * svd.singularValues().maxCoeff()).count();
    std::cout << "rank(B0) = " << rk << "/" << N << "\n";

    double bpbp = (Bp * B * Bp - Bp).norm() / std::max(Bp.norm(), 1e-12);
    std::cout << "||B+BB+-B+||/||B+|| = " << bpbp << (bpbp < 1e-6 ? " [OK]\n" : " [WARN]\n");
}

static void write_mat(const std::string& path, const Eigen::MatrixXd& M) {
    std::ofstream f(path);
    f << "sector"; for (const auto& s : SECTOR_NAMES) f << "," << s; f << "\n";
    for (int i = 0; i < M.rows(); ++i) {
        f << SECTOR_NAMES[i % N];
        for (int j = 0; j < M.cols(); ++j) f << "," << std::fixed << std::setprecision(6) << M(i,j);
        f << "\n";
    }
}

static void write_vec(const std::string& path, const Vec5& v, const std::string& col) {
    std::ofstream f(path);
    f << "sector," << col << "\n";
    for (int j = 0; j < N; ++j)
        f << SECTOR_NAMES[j] << "," << std::fixed << std::setprecision(4) << v[j] << "\n";
}

static void write_beh(const std::string& path, const SectorBehavioral& p) {
    std::ofstream f(path);
    f << "sector,delta,nu,kappa,eta,alpha,p_inn,mu\n" << std::fixed << std::setprecision(6);
    for (int j = 0; j < N; ++j)
        f << SECTOR_NAMES[j] << "," << p.delta[j] << "," << p.nu[j] << "," << p.kappa[j]
          << "," << p.eta[j] << "," << p.alpha[j] << "," << p.p_inn[j] << "," << p.mu[j] << "\n";
}

int main(int argc, char* argv[]) {
    std::string data_dir = "calibration_data", out_dir = "calibration_output";
    if (argc > 1) data_dir = argv[1];
    if (argc > 2) out_dir  = argv[2];
    fs::create_directories(out_dir);

    try {
        Mat5 Z  = read_csv_matrix(data_dir + "/io_flows.csv", N, N).topLeftCorner<N, N>();
        Vec5 X0 = read_csv_vector(data_dir + "/output.csv");
        Mat5 A0 = compute_A(Z, X0);
        Vec5 u0 = ((Mat5::Identity() - A0) * X0).cwiseMax(0.01);

        auto cap = read_csv_matrix(data_dir + "/capital.csv", N, 3);
        double K_total = cap.col(0).mean();
        Vec5 GFCF = cap.col(1), GVA = cap.col(2);

        auto lab = read_csv_matrix(data_dir + "/labour.csv", N, 2);
        Vec5 D1 = lab.col(0), X_avg = lab.col(1);

        Vec5 dX  = read_csv_vector(data_dir + "/dx_series.csv");
        auto sp  = read_csv_matrix(data_dir + "/sector_params.csv", N, 2);
        Vec5 vol = sp.col(0), dm = sp.col(1);

        std::ifstream amf(data_dir + "/macro_scalars.csv");
        std::string ln; std::getline(amf, ln); std::getline(amf, ln);
        double Am = std::stod(ln.substr(ln.find(',') + 1));

        Mat5 B0, Bp; compute_B(build_Q(GFCF, X0), dX, 1e-3, B0, Bp);

        SectorBehavioral params = calibrate_behavioral(GVA, D1, GFCF, X_avg, vol, K_total, Am, dm);
        validate(A0, B0, Bp, X0, u0);

        write_mat(out_dir + "/A0.csv",      A0);
        write_mat(out_dir + "/B0.csv",      B0);
        write_mat(out_dir + "/B_plus.csv",  Bp);
        write_vec(out_dir + "/u0.csv",      u0, "u0_M_EUR");
        write_vec(out_dir + "/X0.csv",      X0, "X0_M_EUR");
        write_beh(out_dir + "/sector_behavioural.csv", params);

        std::ofstream rep(out_dir + "/report.txt");
        rep << "A0:\n";
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) rep << std::setw(9) << std::fixed << std::setprecision(4) << A0(i,j);
            rep << "\n";
        }
        rep << "X0 (M EUR):\n";
        for (int j = 0; j < N; ++j) rep << "  " << SECTOR_NAMES[j] << ": " << X0[j] << "\n";
        rep << "u0 (M EUR):\n";
        for (int j = 0; j < N; ++j) rep << "  " << SECTOR_NAMES[j] << ": " << u0[j] << "\n";

        std::cout << "Done -> " << out_dir << "/\n";
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n"; return 1;
    }
    return 0;
}
