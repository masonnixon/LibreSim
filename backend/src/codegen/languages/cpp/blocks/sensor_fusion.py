"""C++ templates for sensor-fusion tracking blocks."""

from ....models import BlockInfo


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
    "alpha_beta_filter": alpha_beta_filter_template,
    "alpha_beta_gamma_filter": alpha_beta_gamma_filter_template,
}
