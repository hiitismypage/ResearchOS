#include "model.hpp"

#include <cmath>
#include <algorithm>
#include <numeric>
#include <stdexcept>
#include <fstream>
#include <sstream>
#include <iostream>
#include <Eigen/Dense>

static Vec5 leontief_target(const Vec5& x,
                             const Mat5& A,
                             const Mat5& B,
                             const Vec5& u)
{
    Mat5 M = Mat5::Identity() - A - G_U * B;
    Vec5 x_star;
    Eigen::FullPivLU<Mat5> lu(M);
    if (lu.isInvertible()) {
        x_star = lu.solve(u);
    } else {
        Eigen::JacobiSVD<Mat5> svd(M, Eigen::ComputeFullU | Eigen::ComputeFullV);
        x_star = svd.solve(u);
    }
    return x_star.cwiseMax(0.0);
}

static double spectral_radius(const Mat5& A)
{
    Eigen::EigenSolver<Mat5> es(A, false);
    double rho = 0.0;
    for (int i = 0; i < N; ++i) {
        double m = std::abs(es.eigenvalues()(i));
        if (m > rho) rho = m;
    }
    return rho;
}

static double hhi(const VecX& omega)
{
    return omega.squaredNorm();
}

static double balance_residual(const Vec5& x,
                                const Vec5& x_next,
                                const Mat5& A_next,
                                const Mat5& B_next,
                                const Vec5& u)
{
    Vec5 r = x_next - A_next * x_next - B_next * (x_next - x) - u;
    double denom = x_next.norm() + 1e-15;
    return r.norm() / denom;
}

static void step(Model& m,
                 std::mt19937_64& rng,
                 Vec5& x_out,
                 Mat5& A_out,
                 Mat5& B_out,
                 Vec5& i_agg_out)
{
    Vec5 x_star = leontief_target(m.x, m.A, m.B, m.u);

    std::array<VecX, N> x_jf_arr;
    std::array<MatX, N> z_ijf_arr;
    std::array<MatX, N> q_ijf_arr;
    std::array<VecX, N> k_new_arr;
    std::array<VecX, N> theta_new_arr;
    std::array<VecX, N> omega_new_arr;
    std::array<MatX, N> a_f_new_arr;
    std::array<VecX, N> d_e_new_arr;

    std::normal_distribution<double>  norm_dist(0.0, 1.0);
    std::uniform_real_distribution<double> unif_dist(0.0, 1.0);

    for (int j = 0; j < N; ++j) {
        const SectorParams& sp = m.params[j];
        FirmBlock&          fb = m.firms[j];
        int                 Nj = m.n_firms[j];

        VecX d_jf    = fb.omega * x_star(j);
        VecX d_e_new = sp.alpha * fb.d_e + (1.0 - sp.alpha) * d_jf;
        VecX x_bar   = sp.nu * fb.theta.array() * fb.k.array();

        VecX x_jf = d_e_new.cwiseMin(d_jf).cwiseMin(x_bar).cwiseMax(0.0);

        MatX z_ijf = fb.a_f * x_jf.asDiagonal();

        VecX row_sums = z_ijf.colwise().sum();
        VecX pi_jf    = x_jf - row_sums - fb.c_f;

        VecX cap_gap = (d_jf - x_bar).cwiseMax(0.0);
        VecX I_exp   = sp.kappa * pi_jf.cwiseMax(0.0) + sp.eta * cap_gap;

        MatX q_ijf = fb.gamma_f * I_exp.asDiagonal();

        VecX k_new = (fb.k + I_exp).cwiseMax(K_MIN);

        VecX k_safe = fb.k.cwiseMax(K_MIN);
        VecX theta_new = fb.theta.array() *
                         (1.0 + sp.mu * I_exp.array() / k_safe.array());

        MatX a_f_new = fb.a_f;
        for (int f = 0; f < Nj; ++f) {
            if (unif_dist(rng) < sp.p_inn) {
                double reduc = unif_dist(rng) * sp.mu;
                a_f_new.col(f) *= (1.0 - reduc);
                a_f_new.col(f) = a_f_new.col(f).cwiseMax(0.0);
            }
        }

        double x_tot = x_jf.sum();
        VecX omega_new = (x_tot > 1e-9)
                         ? (x_jf / x_tot).eval()
                         : fb.omega;

        x_jf_arr[j]     = x_jf;
        z_ijf_arr[j]     = z_ijf;
        q_ijf_arr[j]     = q_ijf;
        k_new_arr[j]     = k_new;
        theta_new_arr[j] = theta_new;
        omega_new_arr[j] = omega_new;
        a_f_new_arr[j]   = a_f_new;
        d_e_new_arr[j]   = d_e_new;
    }

    for (int j = 0; j < N; ++j) {
        x_out(j) = x_jf_arr[j].sum();
    }

    A_out = Mat5::Zero();
    for (int j = 0; j < N; ++j) {
        double xs = x_jf_arr[j].sum();
        if (xs > 1e-9) {
            for (int i = 0; i < N; ++i) {
                A_out(i, j) = z_ijf_arr[j].row(i).sum() / xs;
            }
        } else {
            A_out.col(j) = m.A.col(j);
        }
    }

    B_out = Mat5::Zero();
    for (int j = 0; j < N; ++j) {
        double dX = std::max(std::abs(x_out(j) - m.x(j)), EPS_B);
        for (int i = 0; i < N; ++i) {
            B_out(i, j) = q_ijf_arr[j].row(i).sum() / dX;
        }
    }

    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            double ceil_val = (m.B0(i, j) > 0.0)
                              ? CLIP_B_FACTOR * m.B0(i, j)
                              : CLIP_B_ABS;
            B_out(i, j) = std::clamp(B_out(i, j), 0.0, ceil_val);
        }
    }

    for (int j = 0; j < N; ++j) {
        m.firms[j].k       = k_new_arr[j];
        m.firms[j].theta   = theta_new_arr[j];
        m.firms[j].omega   = omega_new_arr[j];
        m.firms[j].a_f     = a_f_new_arr[j];
        m.firms[j].d_e     = d_e_new_arr[j];
    }

    i_agg_out = Vec5::Zero();
    for (int j = 0; j < N; ++j) {
        i_agg_out(j) = q_ijf_arr[j].sum();
    }
}

std::vector<TrajectoryRow> run(Model& m, uint64_t seed)
{
    std::mt19937_64 rng(seed);
    std::normal_distribution<double> demand_shock(0.0, SIGMA_U);

    std::vector<TrajectoryRow> traj;
    traj.reserve(T_STEPS + 1);

    for (int t = 0; t <= T_STEPS; ++t) {
        TrajectoryRow row;
        row.t     = t;
        row.year  = 2015 + t;
        row.rho_A = spectral_radius(m.A);
        row.gdp   = m.x.sum();
        row.u_total = m.u.sum();

        double k_total = 0.0;
        for (int j = 0; j < N; ++j) {
            row.x_j[j]     = m.x(j);
            row.k_j[j]     = m.firms[j].k.sum();
            row.theta_j[j] = m.firms[j].theta.mean();
            row.hhi_j[j]   = hhi(m.firms[j].omega);
            row.a_diag[j]  = m.A(j, j);
            k_total        += row.k_j[j];
        }
        row.k_total = k_total;

        if (t == T_STEPS) {
            row.balance_resid = 0.0;
            row.i_total       = 0.0;
            for (int j = 0; j < N; ++j) row.i_j[j] = 0.0;
            traj.push_back(row);
            break;
        }

        Vec5  x_next, i_agg;
        Mat5  A_next, B_next;
        step(m, rng, x_next, A_next, B_next, i_agg);

        row.balance_resid = balance_residual(m.x, x_next, A_next, B_next, m.u);
        row.i_total       = i_agg.sum();
        for (int j = 0; j < N; ++j) row.i_j[j] = i_agg(j);

        for (int j = 0; j < N; ++j) {
            double eps   = demand_shock(rng);
            m.u(j) = std::max(m.u(j) * (1.0 + G_U + eps), 1e-3);
        }

        m.x = x_next;
        m.A = A_next;
        m.B = B_next;

        traj.push_back(row);
    }
    return traj;
}

void save_trajectory(const std::vector<TrajectoryRow>& traj,
                     const std::string& path,
                     const std::array<std::string, N>& sector_names)
{
    std::ofstream f(path);
    f << "t,year,rho_A,GDP_proxy,K_total,U_total,balance_resid,I_total";
    for (auto& s : sector_names)
        f << ",X_" << s << ",K_" << s << ",theta_" << s
          << ",HHI_" << s << ",A_diag_" << s << ",I_" << s;
    f << "\n";
    f << std::fixed;
    f.precision(6);
    for (const auto& r : traj) {
        f << r.t << "," << r.year << ","
          << r.rho_A << "," << r.gdp << "," << r.k_total << ","
          << r.u_total << "," << r.balance_resid << "," << r.i_total;
        for (int j = 0; j < N; ++j)
            f << "," << r.x_j[j] << "," << r.k_j[j] << ","
              << r.theta_j[j] << "," << r.hhi_j[j] << ","
              << r.a_diag[j] << "," << r.i_j[j];
        f << "\n";
    }
}
