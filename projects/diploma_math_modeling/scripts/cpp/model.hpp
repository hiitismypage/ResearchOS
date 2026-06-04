#pragma once

#include <array>
#include <vector>
#include <random>
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

struct TrajectoryRow {
    int    t;
    int    year;
    double rho_A;
    double gdp;
    double k_total;
    double u_total;
    double balance_resid;
    double i_total;
    std::array<double, N> x_j;
    std::array<double, N> k_j;
    std::array<double, N> theta_j;
    std::array<double, N> hhi_j;
    std::array<double, N> a_diag;
    std::array<double, N> i_j;
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
