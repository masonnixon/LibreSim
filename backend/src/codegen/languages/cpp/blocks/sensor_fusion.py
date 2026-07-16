"""C++ templates for sensor-fusion tracking blocks."""

from ....models import BlockInfo
from .sources import _python_random_members


def imu_sensor_template(block: BlockInfo, class_name: str) -> str:
    """Generate an OSK-compatible six-axis IMU model."""
    p = block.parameters
    accel_noise = p.get("accelNoise", p.get("accel_noise", 0.01))
    gyro_noise = p.get("gyroNoise", p.get("gyro_noise", 0.001))
    accel_bias = p.get("accelBias", p.get("accel_bias", [0.0] * 3))
    gyro_bias = p.get("gyroBias", p.get("gyro_bias", [0.0] * 3))
    accel_scale = p.get("accelScaleError", p.get("accel_scale_error", 0.0))
    gyro_scale = p.get("gyroScaleError", p.get("gyro_scale_error", 0.0))
    seed = p.get("seed", None)
    accel_bias_values = ", ".join(str(value) for value in accel_bias)
    gyro_bias_values = ", ".join(str(value) for value in gyro_bias)
    random_members = _python_random_members(seed)
    return f"""
// {block.name} - OSK-compatible six-axis IMU
class {class_name} {{
public:
    std::array<double, 3> input = {{}};
    std::array<double, 3> input1 = {{}};
    std::array<double, 6> output = {{}};
    std::array<double, 3> accel_bias = {{{{{accel_bias_values}}}}};
    std::array<double, 3> gyro_bias = {{{{{gyro_bias_values}}}}};
    double accel_noise = {accel_noise};
    double gyro_noise = {gyro_noise};
    double accel_scale_error = {accel_scale};
    double gyro_scale_error = {gyro_scale};

    void init() {{ output.fill(0.0); }}

    void update(double t) {{
        (void)t;
        for (int i = 0; i < 3; ++i) {{
            output[i] = input[i] * (1.0 + accel_scale_error)
                + accel_bias[i] + gauss(0.0, accel_noise);
        }}
        for (int i = 0; i < 3; ++i) {{
            output[3 + i] = input1[i] * (1.0 + gyro_scale_error)
                + gyro_bias[i] + gauss(0.0, gyro_noise);
        }}
    }}

    double get_output(int port = 0) const {{
        return port >= 0 && port < 6 ? output[port] : 0.0;
    }}

    const std::array<double, 6>& getOutputVector() const {{ return output; }}

{random_members}
}};
"""


def madgwick_filter_template(block: BlockInfo, class_name: str) -> str:
    beta = block.parameters.get("beta", 0.1)
    return f"""
// {block.name} - OSK-compatible Madgwick AHRS
class {class_name} {{
public:
    std::array<double, 3> input = {{}};
    std::array<double, 3> input1 = {{}};
    std::array<double, 4> output = {{1.0, 0.0, 0.0, 0.0}};
    std::array<double, 4> q = {{1.0, 0.0, 0.0, 0.0}};
    double beta = {beta};

    void init() {{ q = {{1.0, 0.0, 0.0, 0.0}}; output = q; }}
    void update(double t, double dt) {{
        (void)t;
        double ax=input[0], ay=input[1], az=input[2];
        double gx=input1[0], gy=input1[1], gz=input1[2];
        double norm=std::sqrt(ax*ax+ay*ay+az*az);
        if (norm>1e-10) {{ ax/=norm; ay/=norm; az/=norm; }} else {{ ax=ay=az=0.0; }}
        double q0=q[0],q1=q[1],q2=q[2],q3=q[3];
        double _2q0=2*q0,_2q1=2*q1,_2q2=2*q2,_2q3=2*q3;
        double _4q0=4*q0,_4q1=4*q1,_4q2=4*q2,_8q1=8*q1,_8q2=8*q2;
        double q0q0=q0*q0,q1q1=q1*q1,q2q2=q2*q2,q3q3=q3*q3;
        double s0=_4q0*q2q2+_2q2*ax+_4q0*q1q1-_2q1*ay;
        double s1=_4q1*q3q3-_2q3*ax+4*q0q0*q1-_2q0*ay-_4q1+_8q1*q1q1+_8q1*q2q2+_4q1*az;
        double s2=4*q0q0*q2+_2q0*ax+_4q2*q3q3-_2q3*ay-_4q2+_8q2*q1q1+_8q2*q2q2+_4q2*az;
        double s3=4*q1q1*q3-_2q1*ax+4*q2q2*q3-_2q2*ay;
        norm=std::sqrt(s0*s0+s1*s1+s2*s2+s3*s3);
        if (norm>1e-10) {{ s0/=norm; s1/=norm; s2/=norm; s3/=norm; }}
        double d0=0.5*(-q1*gx-q2*gy-q3*gz)-beta*s0;
        double d1=0.5*(q0*gx+q2*gz-q3*gy)-beta*s1;
        double d2=0.5*(q0*gy-q1*gz+q3*gx)-beta*s2;
        double d3=0.5*(q0*gz+q1*gy-q2*gx)-beta*s3;
        q0+=d0*dt; q1+=d1*dt; q2+=d2*dt; q3+=d3*dt;
        norm=std::sqrt(q0*q0+q1*q1+q2*q2+q3*q3);
        if (norm>1e-10) q={{q0/norm,q1/norm,q2/norm,q3/norm}};
        output=q;
    }}
    double get_output(int port=0) const {{ return port>=0&&port<4 ? output[port] : 0.0; }}
    const std::array<double,4>& getOutputVector() const {{ return output; }}
}};
"""


def complementary_filter_template(block: BlockInfo, class_name: str) -> str:
    alpha = block.parameters.get("alpha", 0.98)
    return f"""
// {block.name} - OSK-compatible complementary attitude filter
class {class_name} {{
public:
    std::array<double,3> input={{}};
    std::array<double,3> input1={{}};
    std::array<double,3> output={{}};
    std::array<double,3> euler={{}};
    double alpha={alpha};
    void init() {{ euler.fill(0.0); output.fill(0.0); }}
    void update(double t,double dt) {{
        (void)t;
        double ax=input[0],ay=input[1],az=input[2],p=input1[0],qq=input1[1],r=input1[2];
        double roll=euler[0],pitch=euler[1],yaw=euler[2];
        double ar=std::atan2(ay,std::sqrt(ax*ax+az*az));
        double ap=std::atan2(-ax,std::sqrt(ay*ay+az*az));
        double rr=p+std::sin(roll)*std::tan(pitch)*qq+std::cos(roll)*std::tan(pitch)*r;
        double pr=std::cos(roll)*qq-std::sin(roll)*r;
        double yr=std::abs(std::cos(pitch))>1e-6
            ? std::sin(roll)/std::cos(pitch)*qq+std::cos(roll)/std::cos(pitch)*r : 0.0;
        euler={{alpha*(roll+rr*dt)+(1-alpha)*ar,alpha*(pitch+pr*dt)+(1-alpha)*ap,yaw+yr*dt}};
        output=euler;
    }}
    double get_output(int port=0) const {{ return port>=0&&port<3 ? output[port] : 0.0; }}
    const std::array<double,3>& getOutputVector() const {{ return output; }}
}};
"""


def alpha_beta_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate an alpha-beta position and velocity tracking filter."""
    alpha = block.parameters.get("alpha", 0.5)
    beta = block.parameters.get("beta", 0.1)
    sample_time = block.parameters.get("sampleTime", 0.1)
    return f"""
// {block.name} - Alpha-beta tracking filter
#include <array>

class {class_name} {{
public:
    double alpha = {alpha};
    double beta = {beta};
    double sample_time = {sample_time};
    double input = 0.0;
    double position = 0.0;
    double velocity = 0.0;
    std::array<double, 2> output = {{0.0, 0.0}};

    void init() {{
        position = 0.0;
        velocity = 0.0;
        output = {{0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        double predicted_position = position + velocity * sample_time;
        double residual = input - predicted_position;
        position = predicted_position + alpha * residual;
        velocity += (beta / sample_time) * residual;
        output = {{position, velocity}};
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 2) return output[port];
        return 0.0;
    }}
}};
"""


def alpha_beta_gamma_filter_template(block: BlockInfo, class_name: str) -> str:
    """Generate an alpha-beta-gamma position, velocity, and acceleration filter."""
    alpha = block.parameters.get("alpha", 0.5)
    beta = block.parameters.get("beta", 0.3)
    gamma = block.parameters.get("gamma", 0.1)
    sample_time = block.parameters.get("sampleTime", 0.1)
    return f"""
// {block.name} - Alpha-beta-gamma tracking filter
#include <array>

class {class_name} {{
public:
    double alpha = {alpha};
    double beta = {beta};
    double gamma = {gamma};
    double sample_time = {sample_time};
    double input = 0.0;
    double position = 0.0;
    double velocity = 0.0;
    double acceleration = 0.0;
    std::array<double, 3> output = {{0.0, 0.0, 0.0}};

    void init() {{
        position = 0.0;
        velocity = 0.0;
        acceleration = 0.0;
        output = {{0.0, 0.0, 0.0}};
    }}

    void update(double t) {{
        (void)t;
        double dt = sample_time;
        double predicted_position =
            position + velocity * dt + 0.5 * acceleration * dt * dt;
        double predicted_velocity = velocity + acceleration * dt;
        double residual = input - predicted_position;
        position = predicted_position + alpha * residual;
        velocity = predicted_velocity + (beta / dt) * residual;
        acceleration += (2.0 * gamma / (dt * dt)) * residual;
        output = {{position, velocity, acceleration}};
    }}

    double get_output(int port = 0) const {{
        if (port >= 0 && port < 3) return output[port];
        return 0.0;
    }}
}};
"""


SENSOR_FUSION_TEMPLATES = {
    "imu_sensor": imu_sensor_template,
    "madgwick_filter": madgwick_filter_template,
    "complementary_filter": complementary_filter_template,
    "alpha_beta_filter": alpha_beta_filter_template,
    "alpha_beta_gamma_filter": alpha_beta_gamma_filter_template,
}
