"""C templates for sensor-fusion tracking blocks."""

from ....models import BlockInfo
from ....random_compat import python_mt19937_state


def imu_sensor_template(block: BlockInfo, struct_name: str) -> str:
    """Generate an OSK-compatible six-axis IMU model."""
    p = block.parameters
    an = p.get("accelNoise", p.get("accel_noise", 0.01))
    gn = p.get("gyroNoise", p.get("gyro_noise", 0.001))
    ab = p.get("accelBias", p.get("accel_bias", [0.0] * 3))
    gb = p.get("gyroBias", p.get("gyro_bias", [0.0] * 3))
    ase = p.get("accelScaleError", p.get("accel_scale_error", 0.0))
    gse = p.get("gyroScaleError", p.get("gyro_scale_error", 0.0))
    state, index = python_mt19937_state(p.get("seed", None))
    state_values = ", ".join(f"{word}u" for word in state)
    ab_values = ", ".join(str(value) for value in ab)
    gb_values = ", ".join(str(value) for value in gb)
    return f"""
// {block.name} - OSK-compatible six-axis IMU
#include <stdint.h>
#include <stddef.h>
typedef struct {{
    double input[3], input1[3], output[6], accel_bias[3], gyro_bias[3];
    double accel_noise, gyro_noise, accel_scale_error, gyro_scale_error;
    uint32_t mt[624]; size_t mti; int have_spare; double spare;
}} {struct_name};
static const uint32_t {struct_name}_initial_mt[624] = {{{state_values}}};
static uint32_t {struct_name}_mt({struct_name}* b) {{
    if (b->mti >= 624) {{
        for (size_t k=0;k<227;k++) {{ uint32_t y=(b->mt[k]&0x80000000u)|(b->mt[k+1]&0x7fffffffu); b->mt[k]=b->mt[k+397]^(y>>1)^((y&1u)?0x9908b0dfu:0u); }}
        for (size_t k=227;k<623;k++) {{ uint32_t y=(b->mt[k]&0x80000000u)|(b->mt[k+1]&0x7fffffffu); b->mt[k]=b->mt[k-227]^(y>>1)^((y&1u)?0x9908b0dfu:0u); }}
        uint32_t y=(b->mt[623]&0x80000000u)|(b->mt[0]&0x7fffffffu); b->mt[623]=b->mt[396]^(y>>1)^((y&1u)?0x9908b0dfu:0u); b->mti=0;
    }}
    uint32_t y=b->mt[b->mti++]; y^=y>>11; y^=(y<<7)&0x9d2c5680u; y^=(y<<15)&0xefc60000u; y^=y>>18; return y;
}}
static double {struct_name}_random({struct_name}* b) {{ double a={struct_name}_mt(b)>>5, c={struct_name}_mt(b)>>6; return (a*67108864.0+c)/9007199254740992.0; }}
static double {struct_name}_gauss({struct_name}* b,double mu,double sigma) {{
    if (b->have_spare) {{ b->have_spare=0; return mu+sigma*b->spare; }}
    double x={struct_name}_random(b)*6.283185307179586, r=sqrt(-2.0*log(1.0-{struct_name}_random(b)));
    b->spare=sin(x)*r; b->have_spare=1; return mu+sigma*cos(x)*r;
}}
void {struct_name}_init({struct_name}* b) {{
    double ab[3]={{{ab_values}}}, gb[3]={{{gb_values}}};
    for(int i=0;i<3;i++){{b->input[i]=b->input1[i]=0.0;b->accel_bias[i]=ab[i];b->gyro_bias[i]=gb[i];}}
    for(int i=0;i<6;i++)b->output[i]=0.0;
    b->accel_noise={an};b->gyro_noise={gn};b->accel_scale_error={ase};b->gyro_scale_error={gse};
    for(int i=0;i<624;i++)b->mt[i]={struct_name}_initial_mt[i];b->mti={index};b->have_spare=0;b->spare=0.0;
}}
void {struct_name}_update({struct_name}* b,double t) {{
    (void)t;
    for(int i=0;i<3;i++)b->output[i]=b->input[i]*(1+b->accel_scale_error)+b->accel_bias[i]+{struct_name}_gauss(b,0,b->accel_noise);
    for(int i=0;i<3;i++)b->output[3+i]=b->input1[i]*(1+b->gyro_scale_error)+b->gyro_bias[i]+{struct_name}_gauss(b,0,b->gyro_noise);
}}
double {struct_name}_get_output({struct_name}* b,int port){{return port>=0&&port<6?b->output[port]:0.0;}}
static inline double* {struct_name}_get_output_vector({struct_name}* b){{return b->output;}}
"""


def madgwick_filter_template(block: BlockInfo, struct_name: str) -> str:
    beta = block.parameters.get("beta", 0.1)
    return f"""
typedef struct {{double input[3],input1[3],output[4],q[4],beta;}} {struct_name};
void {struct_name}_init({struct_name}*b){{for(int i=0;i<3;i++)b->input[i]=b->input1[i]=0;b->q[0]=b->output[0]=1;b->q[1]=b->q[2]=b->q[3]=b->output[1]=b->output[2]=b->output[3]=0;b->beta={beta};}}
void {struct_name}_update({struct_name}*b,double t,double dt){{
 (void)t;double ax=b->input[0],ay=b->input[1],az=b->input[2],gx=b->input1[0],gy=b->input1[1],gz=b->input1[2],n=sqrt(ax*ax+ay*ay+az*az);if(n>1e-10){{ax/=n;ay/=n;az/=n;}}else ax=ay=az=0;
 double q0=b->q[0],q1=b->q[1],q2=b->q[2],q3=b->q[3],a0=2*q0,a1=2*q1,a2=2*q2,a3=2*q3,c0=4*q0,c1=4*q1,c2=4*q2,e1=8*q1,e2=8*q2,q00=q0*q0,q11=q1*q1,q22=q2*q2,q33=q3*q3;
 double s0=c0*q22+a2*ax+c0*q11-a1*ay,s1=c1*q33-a3*ax+4*q00*q1-a0*ay-c1+e1*q11+e1*q22+c1*az,s2=4*q00*q2+a0*ax+c2*q33-a3*ay-c2+e2*q11+e2*q22+c2*az,s3=4*q11*q3-a1*ax+4*q22*q3-a2*ay;
 n=sqrt(s0*s0+s1*s1+s2*s2+s3*s3);if(n>1e-10){{s0/=n;s1/=n;s2/=n;s3/=n;}}
 double d0=0.5*(-q1*gx-q2*gy-q3*gz)-b->beta*s0,d1=0.5*(q0*gx+q2*gz-q3*gy)-b->beta*s1,d2=0.5*(q0*gy-q1*gz+q3*gx)-b->beta*s2,d3=0.5*(q0*gz+q1*gy-q2*gx)-b->beta*s3;q0+=d0*dt;q1+=d1*dt;q2+=d2*dt;q3+=d3*dt;
 n=sqrt(q0*q0+q1*q1+q2*q2+q3*q3);if(n>1e-10){{b->q[0]=q0/n;b->q[1]=q1/n;b->q[2]=q2/n;b->q[3]=q3/n;}}for(int i=0;i<4;i++)b->output[i]=b->q[i];}}
double {struct_name}_get_output({struct_name}*b,int p){{return p>=0&&p<4?b->output[p]:0;}}static inline double* {struct_name}_get_output_vector({struct_name}*b){{return b->output;}}
"""


def complementary_filter_template(block: BlockInfo, struct_name: str) -> str:
    alpha = block.parameters.get("alpha", 0.98)
    return f"""
typedef struct {{double input[3],input1[3],output[3],euler[3],alpha;}} {struct_name};
void {struct_name}_init({struct_name}*b){{for(int i=0;i<3;i++)b->input[i]=b->input1[i]=b->output[i]=b->euler[i]=0;b->alpha={alpha};}}
void {struct_name}_update({struct_name}*b,double t,double dt){{(void)t;double ax=b->input[0],ay=b->input[1],az=b->input[2],p=b->input1[0],q=b->input1[1],r=b->input1[2],ro=b->euler[0],pi=b->euler[1],ya=b->euler[2],ar=atan2(ay,sqrt(ax*ax+az*az)),ap=atan2(-ax,sqrt(ay*ay+az*az)),rr=p+sin(ro)*tan(pi)*q+cos(ro)*tan(pi)*r,pr=cos(ro)*q-sin(ro)*r,yr=fabs(cos(pi))>1e-6?sin(ro)/cos(pi)*q+cos(ro)/cos(pi)*r:0;b->euler[0]=b->alpha*(ro+rr*dt)+(1-b->alpha)*ar;b->euler[1]=b->alpha*(pi+pr*dt)+(1-b->alpha)*ap;b->euler[2]=ya+yr*dt;for(int i=0;i<3;i++)b->output[i]=b->euler[i];}}
double {struct_name}_get_output({struct_name}*b,int p){{return p>=0&&p<3?b->output[p]:0;}}static inline double* {struct_name}_get_output_vector({struct_name}*b){{return b->output;}}
"""


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
    "imu_sensor": imu_sensor_template,
    "madgwick_filter": madgwick_filter_template,
    "complementary_filter": complementary_filter_template,
    "alpha_beta_filter": alpha_beta_filter_template,
    "alpha_beta_gamma_filter": alpha_beta_gamma_filter_template,
}
