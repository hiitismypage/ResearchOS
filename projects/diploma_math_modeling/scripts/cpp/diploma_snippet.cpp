#include <array>
#include <cmath>
#include <random>
#include <algorithm>
#include <Eigen/Dense>

static constexpr int    N             = 5;
static constexpr int    T_STEPS       = 30;
static constexpr double G_U           = 0.015;
static constexpr double SIGMA_U       = 0.020;
static constexpr double EPS_B         = 1.0;
static constexpr double CLIP_B_FACTOR = 5.0;
static constexpr double CLIP_B_ABS    = 1.0;
static constexpr double K_MIN         = 1e-4;

using Mat5 = Eigen::Matrix<double, N, N>;
using Vec5 = Eigen::Matrix<double, N, 1>;
using MatX = Eigen::MatrixXd;
using VecX = Eigen::VectorXd;

struct SectorParams {
    double delta;
    double nu;
    double kappa;
    double eta;
    double alpha;
    double p_inn;
    double mu;
};

struct FirmBlock {
    VecX k;
    VecX theta;
    VecX omega;
    VecX d_e;
    VecX c_f;
    MatX a_f;
    MatX gamma_f;
};

struct Model {
    Vec5  x;
    Vec5  u;
    Mat5  A;
    Mat5  B;
    Mat5  B0;
    std::array<FirmBlock,    N> firms;
    std::array<SectorParams, N> params;
    std::array<int,          N> n_firms;
};

Vec5 leontief_target(const Vec5& x,
                     const Mat5& A,
                     const Mat5& B,
                     const Vec5& u)
{
    Mat5 M = Mat5::Identity() - A - G_U * B;
    Eigen::FullPivLU<Mat5> lu(M);
    Vec5 x_star;
    if (lu.isInvertible()) {
        x_star = lu.solve(u);
    } else {
        Eigen::JacobiSVD<Mat5> svd(M,
            Eigen::ComputeFullU | Eigen::ComputeFullV);
        x_star = svd.solve(u);
    }
    return x_star.cwiseMax(0.0);
}

void step(Model&          m,
          std::mt19937_64& rng,
          Vec5&            x_out,
          Mat5&            A_out,
          Mat5&            B_out,
          Vec5&            i_agg_out)
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

    std::uniform_real_distribution<double> unif(0.0, 1.0);

    for (int j = 0; j < N; ++j) {
        const SectorParams& sp = m.params[j];
        FirmBlock&          fb = m.firms[j];
        int                 Nj = m.n_firms[j];

        VecX d_jf    = fb.omega * x_star(j);
        VecX d_e_new = sp.alpha * fb.d_e
                       + (1.0 - sp.alpha) * d_jf;

        VecX x_bar   = sp.nu
                       * fb.theta.array()
                       * fb.k.array();

        VecX x_jf = d_e_new
                    .cwiseMin(d_jf)
                    .cwiseMin(x_bar)
                    .cwiseMax(0.0);

        MatX z_ijf = fb.a_f * x_jf.asDiagonal();

        VecX col_sums = z_ijf.colwise().sum();
        VecX pi_jf    = x_jf - col_sums - fb.c_f;

        VecX cap_gap = (d_jf - x_bar).cwiseMax(0.0);
        VecX I_exp   = sp.kappa * pi_jf.cwiseMax(0.0)
                       + sp.eta  * cap_gap;

        MatX q_ijf   = fb.gamma_f * I_exp.asDiagonal();

        VecX k_new     = (fb.k + I_exp).cwiseMax(K_MIN);
        VecX k_safe    = fb.k.cwiseMax(K_MIN);
        VecX theta_new = fb.theta.array()
                         * (1.0 + sp.mu * I_exp.array()
                                        / k_safe.array());

        MatX a_f_new = fb.a_f;
        for (int f = 0; f < Nj; ++f) {
            if (unif(rng) < sp.p_inn) {
                double shock = unif(rng) * sp.mu;
                a_f_new.col(f) =
                    (a_f_new.col(f) * (1.0 - shock))
                    .cwiseMax(0.0);
            }
        }

        double x_tot  = x_jf.sum();
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

    for (int j = 0; j < N; ++j)
        x_out(j) = x_jf_arr[j].sum();

    A_out = Mat5::Zero();
    for (int j = 0; j < N; ++j) {
        double xs = x_jf_arr[j].sum();
        if (xs > 1e-9) {
            for (int i = 0; i < N; ++i)
                A_out(i, j) =
                    z_ijf_arr[j].row(i).sum() / xs;
        } else {
            A_out.col(j) = m.A.col(j);
        }
    }

    B_out = Mat5::Zero();
    for (int j = 0; j < N; ++j) {
        double dX = std::max(
            std::abs(x_out(j) - m.x(j)), EPS_B);
        for (int i = 0; i < N; ++i)
            B_out(i, j) =
                q_ijf_arr[j].row(i).sum() / dX;
    }

    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j) {
            double ceil_val =
                (m.B0(i, j) > 0.0)
                ? CLIP_B_FACTOR * m.B0(i, j)
                : CLIP_B_ABS;
            B_out(i, j) =
                std::clamp(B_out(i, j), 0.0, ceil_val);
        }

    for (int j = 0; j < N; ++j) {
        m.firms[j].k       = k_new_arr[j];
        m.firms[j].theta   = theta_new_arr[j];
        m.firms[j].omega   = omega_new_arr[j];
        m.firms[j].a_f     = a_f_new_arr[j];
        m.firms[j].d_e     = d_e_new_arr[j];
    }

    i_agg_out = Vec5::Zero();
    for (int j = 0; j < N; ++j)
        i_agg_out(j) = q_ijf_arr[j].sum();
}

void run(Model& m, uint64_t seed)
{
    std::mt19937_64 rng(seed);
    std::normal_distribution<double> shock_dist(0.0, SIGMA_U);

    for (int t = 0; t < T_STEPS; ++t) {
        Vec5 x_next, i_agg;
        Mat5 A_next, B_next;

        step(m, rng, x_next, A_next, B_next, i_agg);

        for (int j = 0; j < N; ++j) {
            double eps = shock_dist(rng);
            m.u(j) = std::max(
                m.u(j) * (1.0 + G_U + eps), 1e-3);
        }

        m.x = x_next;
        m.A = A_next;
        m.B = B_next;
    }
}
