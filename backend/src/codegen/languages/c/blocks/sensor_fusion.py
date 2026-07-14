"""C templates for sensor-fusion tracking blocks."""

from ....models import BlockInfo


def alpha_beta_filter_template(block: BlockInfo, struct_name: str) -> str:
    """Generate an alpha-beta position and velocity tracking filter."""
    alpha = block.parameters.get("alpha", 0.5)
    beta = block.parameters.get("beta", 0.1)
    sample_time = block.parameters.get("sampleTime", 0.1)
    return f"""
// {block.name} - Alpha-beta tracking filter
typedef struct {{
    double alpha;
    double beta;
    double sample_time;
    double input;
    double position;
    double velocity;
    double output[2];
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->alpha = {alpha};
    b->beta = {beta};
    b->sample_time = {sample_time};
    b->input = 0.0;
    b->position = 0.0;
    b->velocity = 0.0;
    b->output[0] = 0.0;
    b->output[1] = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double predicted_position = b->position + b->velocity * b->sample_time;
    double residual = b->input - predicted_position;
    b->position = predicted_position + b->alpha * residual;
    b->velocity += (b->beta / b->sample_time) * residual;
    b->output[0] = b->position;
    b->output[1] = b->velocity;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 2) return b->output[port];
    return 0.0;
}}
"""


def alpha_beta_gamma_filter_template(block: BlockInfo, struct_name: str) -> str:
    """Generate an alpha-beta-gamma position, velocity, and acceleration filter."""
    alpha = block.parameters.get("alpha", 0.5)
    beta = block.parameters.get("beta", 0.3)
    gamma = block.parameters.get("gamma", 0.1)
    sample_time = block.parameters.get("sampleTime", 0.1)
    return f"""
// {block.name} - Alpha-beta-gamma tracking filter
typedef struct {{
    double alpha;
    double beta;
    double gamma;
    double sample_time;
    double input;
    double position;
    double velocity;
    double acceleration;
    double output[3];
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->alpha = {alpha};
    b->beta = {beta};
    b->gamma = {gamma};
    b->sample_time = {sample_time};
    b->input = 0.0;
    b->position = 0.0;
    b->velocity = 0.0;
    b->acceleration = 0.0;
    b->output[0] = 0.0;
    b->output[1] = 0.0;
    b->output[2] = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    double dt = b->sample_time;
    double predicted_position =
        b->position + b->velocity * dt + 0.5 * b->acceleration * dt * dt;
    double predicted_velocity = b->velocity + b->acceleration * dt;
    double residual = b->input - predicted_position;
    b->position = predicted_position + b->alpha * residual;
    b->velocity = predicted_velocity + (b->beta / dt) * residual;
    b->acceleration += (2.0 * b->gamma / (dt * dt)) * residual;
    b->output[0] = b->position;
    b->output[1] = b->velocity;
    b->output[2] = b->acceleration;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port >= 0 && port < 3) return b->output[port];
    return 0.0;
}}
"""


SENSOR_FUSION_TEMPLATES = {
    "alpha_beta_filter": alpha_beta_filter_template,
    "alpha_beta_gamma_filter": alpha_beta_gamma_filter_template,
}
