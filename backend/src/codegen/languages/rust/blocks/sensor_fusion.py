"""Rust templates for sensor-fusion tracking blocks."""

from ....models import BlockInfo
from ....random_compat import python_mt19937_state


def imu_sensor_template(block: BlockInfo, struct_name: str) -> str:
    p = block.parameters
    an = p.get("accelNoise", p.get("accel_noise", 0.01))
    gn = p.get("gyroNoise", p.get("gyro_noise", 0.001))
    ab = p.get("accelBias", p.get("accel_bias", [0.0] * 3))
    gb = p.get("gyroBias", p.get("gyro_bias", [0.0] * 3))
    ase = p.get("accelScaleError", p.get("accel_scale_error", 0.0))
    gse = p.get("gyroScaleError", p.get("gyro_scale_error", 0.0))
    state, index = python_mt19937_state(p.get("seed", None))
    mt = ", ".join(f"{x}u32" for x in state)
    av = ", ".join(f"{x}_f64" for x in ab)
    gv = ", ".join(f"{x}_f64" for x in gb)
    return f"""
#[derive(Clone)]
pub struct {struct_name} {{pub input:[f64;3],pub input1:[f64;3],pub output:[f64;6],accel_bias:[f64;3],gyro_bias:[f64;3],accel_noise:f64,gyro_noise:f64,accel_scale:f64,gyro_scale:f64,mt:[u32;624],mti:usize,spare:f64,has_spare:bool}}
impl {struct_name} {{
 pub fn new()->Self{{Self{{input:[0.0;3],input1:[0.0;3],output:[0.0;6],accel_bias:[{av}],gyro_bias:[{gv}],accel_noise:{an}_f64,gyro_noise:{gn}_f64,accel_scale:{ase}_f64,gyro_scale:{gse}_f64,mt:[{mt}],mti:{index},spare:0.0,has_spare:false}}}}
 fn mt_rand(&mut self)->u32{{if self.mti>=624{{for k in 0..227{{let y=(self.mt[k]&0x80000000)|(self.mt[k+1]&0x7fffffff);self.mt[k]=self.mt[k+397]^(y>>1)^if y&1!=0{{0x9908b0df}}else{{0}};}}for k in 227..623{{let y=(self.mt[k]&0x80000000)|(self.mt[k+1]&0x7fffffff);self.mt[k]=self.mt[k-227]^(y>>1)^if y&1!=0{{0x9908b0df}}else{{0}};}}let y=(self.mt[623]&0x80000000)|(self.mt[0]&0x7fffffff);self.mt[623]=self.mt[396]^(y>>1)^if y&1!=0{{0x9908b0df}}else{{0}};self.mti=0;}}let mut y=self.mt[self.mti];self.mti+=1;y^=y>>11;y^=(y<<7)&0x9d2c5680;y^=(y<<15)&0xefc60000;y^=y>>18;y}}
 fn random(&mut self)->f64{{let a=(self.mt_rand()>>5)as f64;let b=(self.mt_rand()>>6)as f64;(a*67108864.0+b)/9007199254740992.0}}
 fn gauss(&mut self,mu:f64,sigma:f64)->f64{{if self.has_spare{{self.has_spare=false;return mu+sigma*self.spare;}}let x=self.random()*std::f64::consts::TAU;let r=(-2.0*(1.0-self.random()).ln()).sqrt();self.spare=x.sin()*r;self.has_spare=true;mu+sigma*x.cos()*r}}
 pub fn init(&mut self){{self.output=[0.0;6];}}
 pub fn update(&mut self,_t:f64){{for i in 0..3{{let v=self.input[i]*(1.0+self.accel_scale)+self.accel_bias[i]+self.gauss(0.0,self.accel_noise);self.output[i]=v;}}for i in 0..3{{let v=self.input1[i]*(1.0+self.gyro_scale)+self.gyro_bias[i]+self.gauss(0.0,self.gyro_noise);self.output[3+i]=v;}}}}
 pub fn get_output(&self,p:usize)->f64{{if p<6{{self.output[p]}}else{{0.0}}}} pub fn get_output_vector(&self)->&[f64;6]{{&self.output}}
}}
impl Default for {struct_name}{{fn default()->Self{{Self::new()}}}}
"""


def madgwick_filter_template(block: BlockInfo, struct_name: str) -> str:
    beta=block.parameters.get("beta",0.1)
    return f"""
#[derive(Clone)] pub struct {struct_name}{{pub input:[f64;3],pub input1:[f64;3],pub output:[f64;4],q:[f64;4],beta:f64}}
impl {struct_name}{{pub fn new()->Self{{Self{{input:[0.0;3],input1:[0.0;3],output:[1.0,0.0,0.0,0.0],q:[1.0,0.0,0.0,0.0],beta:{beta}_f64}}}}pub fn init(&mut self){{self.q=[1.0,0.0,0.0,0.0];self.output=self.q;}}
pub fn update(&mut self,_t:f64,dt:f64){{let(mut ax,mut ay,mut az)=(self.input[0],self.input[1],self.input[2]);let(gx,gy,gz)=(self.input1[0],self.input1[1],self.input1[2]);let mut n=(ax*ax+ay*ay+az*az).sqrt();if n>1e-10{{ax/=n;ay/=n;az/=n;}}else{{ax=0.0;ay=0.0;az=0.0;}}let(mut q0,mut q1,mut q2,mut q3)=(self.q[0],self.q[1],self.q[2],self.q[3]);let(a0,a1,a2,a3)=(2.0*q0,2.0*q1,2.0*q2,2.0*q3);let(c0,c1,c2,e1,e2)=(4.0*q0,4.0*q1,4.0*q2,8.0*q1,8.0*q2);let(q00,q11,q22,q33)=(q0*q0,q1*q1,q2*q2,q3*q3);let(mut s0,mut s1,mut s2,mut s3)=(c0*q22+a2*ax+c0*q11-a1*ay,c1*q33-a3*ax+4.0*q00*q1-a0*ay-c1+e1*q11+e1*q22+c1*az,4.0*q00*q2+a0*ax+c2*q33-a3*ay-c2+e2*q11+e2*q22+c2*az,4.0*q11*q3-a1*ax+4.0*q22*q3-a2*ay);n=(s0*s0+s1*s1+s2*s2+s3*s3).sqrt();if n>1e-10{{s0/=n;s1/=n;s2/=n;s3/=n;}}let(d0,d1,d2,d3)=(0.5*(-q1*gx-q2*gy-q3*gz)-self.beta*s0,0.5*(q0*gx+q2*gz-q3*gy)-self.beta*s1,0.5*(q0*gy-q1*gz+q3*gx)-self.beta*s2,0.5*(q0*gz+q1*gy-q2*gx)-self.beta*s3);q0+=d0*dt;q1+=d1*dt;q2+=d2*dt;q3+=d3*dt;n=(q0*q0+q1*q1+q2*q2+q3*q3).sqrt();if n>1e-10{{self.q=[q0/n,q1/n,q2/n,q3/n];}}self.output=self.q;}}
pub fn get_output(&self,p:usize)->f64{{if p<4{{self.output[p]}}else{{0.0}}}}pub fn get_output_vector(&self)->&[f64;4]{{&self.output}}}}
impl Default for {struct_name}{{fn default()->Self{{Self::new()}}}}
"""


def complementary_filter_template(block: BlockInfo, struct_name: str) -> str:
    alpha=block.parameters.get("alpha",0.98)
    return f"""
#[derive(Clone)]pub struct {struct_name}{{pub input:[f64;3],pub input1:[f64;3],pub output:[f64;3],euler:[f64;3],alpha:f64}}
impl {struct_name}{{pub fn new()->Self{{Self{{input:[0.0;3],input1:[0.0;3],output:[0.0;3],euler:[0.0;3],alpha:{alpha}_f64}}}}pub fn init(&mut self){{self.euler=[0.0;3];self.output=[0.0;3];}}pub fn update(&mut self,_t:f64,dt:f64){{let(ax,ay,az)=(self.input[0],self.input[1],self.input[2]);let(p,q,r)=(self.input1[0],self.input1[1],self.input1[2]);let(ro,pi,ya)=(self.euler[0],self.euler[1],self.euler[2]);let ar=ay.atan2((ax*ax+az*az).sqrt());let ap=(-ax).atan2((ay*ay+az*az).sqrt());let rr=p+ro.sin()*pi.tan()*q+ro.cos()*pi.tan()*r;let pr=ro.cos()*q-ro.sin()*r;let yr=if pi.cos().abs()>1e-6{{ro.sin()/pi.cos()*q+ro.cos()/pi.cos()*r}}else{{0.0}};self.euler=[self.alpha*(ro+rr*dt)+(1.0-self.alpha)*ar,self.alpha*(pi+pr*dt)+(1.0-self.alpha)*ap,ya+yr*dt];self.output=self.euler;}}pub fn get_output(&self,p:usize)->f64{{if p<3{{self.output[p]}}else{{0.0}}}}pub fn get_output_vector(&self)->&[f64;3]{{&self.output}}}}
impl Default for {struct_name}{{fn default()->Self{{Self::new()}}}}
"""


def alpha_beta_filter_template(block: BlockInfo, struct_name: str) -> str:
    """Generate an alpha-beta position and velocity tracking filter."""
    alpha = block.parameters.get("alpha", 0.5)
    beta = block.parameters.get("beta", 0.1)
    sample_time = block.parameters.get("sampleTime", 0.1)
    return f"""
/// {block.name} - Alpha-beta tracking filter
#[derive(Clone)]
pub struct {struct_name} {{
    pub alpha: f64,
    pub beta: f64,
    pub sample_time: f64,
    pub input: f64,
    pub position: f64,
    pub velocity: f64,
    pub output: [f64; 2],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            alpha: {alpha},
            beta: {beta},
            sample_time: {sample_time},
            input: 0.0,
            position: 0.0,
            velocity: 0.0,
            output: [0.0, 0.0],
        }}
    }}

    pub fn init(&mut self) {{
        self.position = 0.0;
        self.velocity = 0.0;
        self.output = [0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let predicted_position = self.position + self.velocity * self.sample_time;
        let residual = self.input - predicted_position;
        self.position = predicted_position + self.alpha * residual;
        self.velocity += (self.beta / self.sample_time) * residual;
        self.output = [self.position, self.velocity];
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        if port < 2 {{ self.output[port] }} else {{ 0.0 }}
    }}
}}
"""


def alpha_beta_gamma_filter_template(block: BlockInfo, struct_name: str) -> str:
    """Generate an alpha-beta-gamma position, velocity, and acceleration filter."""
    alpha = block.parameters.get("alpha", 0.5)
    beta = block.parameters.get("beta", 0.3)
    gamma = block.parameters.get("gamma", 0.1)
    sample_time = block.parameters.get("sampleTime", 0.1)
    return f"""
/// {block.name} - Alpha-beta-gamma tracking filter
#[derive(Clone)]
pub struct {struct_name} {{
    pub alpha: f64,
    pub beta: f64,
    pub gamma: f64,
    pub sample_time: f64,
    pub input: f64,
    pub position: f64,
    pub velocity: f64,
    pub acceleration: f64,
    pub output: [f64; 3],
}}

impl {struct_name} {{
    pub fn new() -> Self {{
        Self {{
            alpha: {alpha},
            beta: {beta},
            gamma: {gamma},
            sample_time: {sample_time},
            input: 0.0,
            position: 0.0,
            velocity: 0.0,
            acceleration: 0.0,
            output: [0.0, 0.0, 0.0],
        }}
    }}

    pub fn init(&mut self) {{
        self.position = 0.0;
        self.velocity = 0.0;
        self.acceleration = 0.0;
        self.output = [0.0, 0.0, 0.0];
    }}

    pub fn update(&mut self, _t: f64) {{
        let dt = self.sample_time;
        let predicted_position =
            self.position + self.velocity * dt + 0.5 * self.acceleration * dt * dt;
        let predicted_velocity = self.velocity + self.acceleration * dt;
        let residual = self.input - predicted_position;
        self.position = predicted_position + self.alpha * residual;
        self.velocity = predicted_velocity + (self.beta / dt) * residual;
        self.acceleration += (2.0 * self.gamma / (dt * dt)) * residual;
        self.output = [self.position, self.velocity, self.acceleration];
    }}

    pub fn get_output(&self, port: usize) -> f64 {{
        if port < 3 {{ self.output[port] }} else {{ 0.0 }}
    }}
}}
"""


SENSOR_FUSION_TEMPLATES = {
    "imu_sensor": imu_sensor_template,
    "madgwick_filter": madgwick_filter_template,
    "complementary_filter": complementary_filter_template,
    "alpha_beta_filter": alpha_beta_filter_template,
    "alpha_beta_gamma_filter": alpha_beta_gamma_filter_template,
}
