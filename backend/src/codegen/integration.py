"""Integration method code generators for all languages."""

from .models import IntegrationMethod


class IntegrationCodeGenerator:
    """Generate integration method code for each language."""

    # Number of passes for each method
    PASSES = {
        IntegrationMethod.EULER: 1,
        IntegrationMethod.RK2: 2,
        IntegrationMethod.RK4: 4,
        IntegrationMethod.MERSON: 5,
    }

    @classmethod
    def get_passes(cls, method: IntegrationMethod) -> int:
        """Get number of passes for an integration method."""
        return cls.PASSES.get(method, 1)

    # =========================================================================
    # Python Integration Methods
    # =========================================================================

    @staticmethod
    def generate_python_euler() -> str:
        return '''
def euler_propagate(integrators: list, dt: float, kpass: int) -> None:
    """Euler integration (single pass)."""
    for integ in integrators:
        integ.state += dt * integ.derivative
'''

    @staticmethod
    def generate_python_rk2() -> str:
        return '''
def rk2_propagate(integrators: list, dt: float, kpass: int) -> None:
    """RK2 (midpoint) integration."""
    for integ in integrators:
        if kpass == 0:
            integ.x0 = integ.state
            integ.xd0 = integ.derivative
            integ.state = integ.x0 + dt / 2.0 * integ.xd0
        elif kpass == 1:
            integ.xd1 = integ.derivative
            integ.state = integ.x0 + dt * integ.xd1
'''

    @staticmethod
    def generate_python_rk4() -> str:
        return '''
def rk4_propagate(integrators: list, dt: float, kpass: int) -> None:
    """RK4 (4th order Runge-Kutta) integration."""
    for integ in integrators:
        if kpass == 0:
            integ.x0 = integ.state
            integ.xd0 = integ.derivative
            integ.state = integ.x0 + dt / 2.0 * integ.xd0
        elif kpass == 1:
            integ.xd1 = integ.derivative
            integ.state = integ.x0 + dt / 2.0 * integ.xd1
        elif kpass == 2:
            integ.xd2 = integ.derivative
            integ.state = integ.x0 + dt * integ.xd2
        elif kpass == 3:
            integ.xd3 = integ.derivative
            integ.state = integ.x0 + dt / 6.0 * (
                integ.xd0 + 2.0 * integ.xd1 + 2.0 * integ.xd2 + integ.xd3
            )
'''

    @staticmethod
    def generate_python_merson() -> str:
        return '''
def merson_propagate(integrators: list, dt: float, kpass: int) -> None:
    """Merson (4th order with error estimation) integration."""
    for integ in integrators:
        if kpass == 0:
            integ.x0 = integ.state
            integ.xd0 = integ.derivative
            integ.state = integ.x0 + dt / 3.0 * integ.xd0
        elif kpass == 1:
            integ.xd1 = integ.derivative
            integ.state = integ.x0 + dt / 6.0 * (integ.xd0 + integ.xd1)
        elif kpass == 2:
            integ.xd2 = integ.derivative
            integ.state = integ.x0 + dt / 8.0 * (integ.xd0 + 3.0 * integ.xd2)
        elif kpass == 3:
            integ.xd3 = integ.derivative
            integ.state = integ.x0 + dt / 2.0 * (integ.xd0 - 3.0 * integ.xd2 + 4.0 * integ.xd3)
        elif kpass == 4:
            integ.xd4 = integ.derivative
            integ.state = integ.x0 + dt / 6.0 * (integ.xd0 + 4.0 * integ.xd3 + integ.xd4)
'''

    @staticmethod
    def generate_python_all() -> str:
        """Generate all Python integration methods."""
        return f'''
# Integration Methods
# ===================

{IntegrationCodeGenerator.generate_python_euler()}

{IntegrationCodeGenerator.generate_python_rk2()}

{IntegrationCodeGenerator.generate_python_rk4()}

{IntegrationCodeGenerator.generate_python_merson()}


def get_propagate_function(method: str):
    """Get the propagation function for an integration method."""
    methods = {{
        "euler": euler_propagate,
        "rk2": rk2_propagate,
        "rk4": rk4_propagate,
        "merson": merson_propagate,
    }}
    return methods.get(method.lower(), rk4_propagate)


def get_num_passes(method: str) -> int:
    """Get the number of passes for an integration method."""
    passes = {{
        "euler": 1,
        "rk2": 2,
        "rk4": 4,
        "merson": 5,
    }}
    return passes.get(method.lower(), 4)
'''

    # =========================================================================
    # C Integration Methods
    # =========================================================================

    @staticmethod
    def generate_c_header() -> str:
        return '''
#ifndef INTEGRATION_H
#define INTEGRATION_H

#include <stddef.h>

// Integrator state structure
typedef struct {
    double* state_ptr;      // Pointer to current state
    double* deriv_ptr;      // Pointer to derivative
    double x0;              // Initial state for this step
    double xd0, xd1, xd2, xd3, xd4;  // Intermediate derivatives
} IntegratorState;

// Integration method enum
typedef enum {
    INTEGRATION_EULER = 0,
    INTEGRATION_RK2 = 1,
    INTEGRATION_RK4 = 2,
    INTEGRATION_MERSON = 3
} IntegrationMethod;

// Get number of passes for a method
int integration_get_passes(IntegrationMethod method);

// Propagate integrators for one pass
void integration_propagate(IntegratorState* states, size_t n_states,
                          double dt, int kpass, IntegrationMethod method);

#endif // INTEGRATION_H
'''

    @staticmethod
    def generate_c_source() -> str:
        return '''
#include "integration.h"

int integration_get_passes(IntegrationMethod method) {
    switch (method) {
        case INTEGRATION_EULER: return 1;
        case INTEGRATION_RK2: return 2;
        case INTEGRATION_RK4: return 4;
        case INTEGRATION_MERSON: return 5;
        default: return 4;
    }
}

static void euler_propagate(IntegratorState* states, size_t n_states, double dt, int kpass) {
    for (size_t i = 0; i < n_states; i++) {
        IntegratorState* s = &states[i];
        *s->state_ptr += dt * (*s->deriv_ptr);
    }
}

static void rk2_propagate(IntegratorState* states, size_t n_states, double dt, int kpass) {
    for (size_t i = 0; i < n_states; i++) {
        IntegratorState* s = &states[i];
        if (kpass == 0) {
            s->x0 = *s->state_ptr;
            s->xd0 = *s->deriv_ptr;
            *s->state_ptr = s->x0 + dt / 2.0 * s->xd0;
        } else if (kpass == 1) {
            s->xd1 = *s->deriv_ptr;
            *s->state_ptr = s->x0 + dt * s->xd1;
        }
    }
}

static void rk4_propagate(IntegratorState* states, size_t n_states, double dt, int kpass) {
    for (size_t i = 0; i < n_states; i++) {
        IntegratorState* s = &states[i];
        if (kpass == 0) {
            s->x0 = *s->state_ptr;
            s->xd0 = *s->deriv_ptr;
            *s->state_ptr = s->x0 + dt / 2.0 * s->xd0;
        } else if (kpass == 1) {
            s->xd1 = *s->deriv_ptr;
            *s->state_ptr = s->x0 + dt / 2.0 * s->xd1;
        } else if (kpass == 2) {
            s->xd2 = *s->deriv_ptr;
            *s->state_ptr = s->x0 + dt * s->xd2;
        } else if (kpass == 3) {
            s->xd3 = *s->deriv_ptr;
            *s->state_ptr = s->x0 + dt / 6.0 * (s->xd0 + 2.0*s->xd1 + 2.0*s->xd2 + s->xd3);
        }
    }
}

static void merson_propagate(IntegratorState* states, size_t n_states, double dt, int kpass) {
    for (size_t i = 0; i < n_states; i++) {
        IntegratorState* s = &states[i];
        if (kpass == 0) {
            s->x0 = *s->state_ptr;
            s->xd0 = *s->deriv_ptr;
            *s->state_ptr = s->x0 + dt / 3.0 * s->xd0;
        } else if (kpass == 1) {
            s->xd1 = *s->deriv_ptr;
            *s->state_ptr = s->x0 + dt / 6.0 * (s->xd0 + s->xd1);
        } else if (kpass == 2) {
            s->xd2 = *s->deriv_ptr;
            *s->state_ptr = s->x0 + dt / 8.0 * (s->xd0 + 3.0 * s->xd2);
        } else if (kpass == 3) {
            s->xd3 = *s->deriv_ptr;
            *s->state_ptr = s->x0 + dt / 2.0 * (s->xd0 - 3.0*s->xd2 + 4.0*s->xd3);
        } else if (kpass == 4) {
            s->xd4 = *s->deriv_ptr;
            *s->state_ptr = s->x0 + dt / 6.0 * (s->xd0 + 4.0*s->xd3 + s->xd4);
        }
    }
}

void integration_propagate(IntegratorState* states, size_t n_states,
                          double dt, int kpass, IntegrationMethod method) {
    switch (method) {
        case INTEGRATION_EULER:
            euler_propagate(states, n_states, dt, kpass);
            break;
        case INTEGRATION_RK2:
            rk2_propagate(states, n_states, dt, kpass);
            break;
        case INTEGRATION_RK4:
            rk4_propagate(states, n_states, dt, kpass);
            break;
        case INTEGRATION_MERSON:
            merson_propagate(states, n_states, dt, kpass);
            break;
    }
}
'''

    # =========================================================================
    # Rust Integration Methods
    # =========================================================================

    @staticmethod
    def generate_rust() -> str:
        return '''
//! Integration methods for numerical simulation

/// Integration method enum
#[derive(Clone, Copy, Debug)]
pub enum IntegrationMethod {
    Euler,
    Rk2,
    Rk4,
    Merson,
}

impl IntegrationMethod {
    /// Get the number of passes for this method
    pub fn passes(&self) -> usize {
        match self {
            IntegrationMethod::Euler => 1,
            IntegrationMethod::Rk2 => 2,
            IntegrationMethod::Rk4 => 4,
            IntegrationMethod::Merson => 5,
        }
    }
}

/// State for an integrator during multi-pass integration
#[derive(Clone, Default)]
pub struct IntegratorState {
    pub state: f64,
    pub derivative: f64,
    pub x0: f64,
    pub xd0: f64,
    pub xd1: f64,
    pub xd2: f64,
    pub xd3: f64,
    pub xd4: f64,
}

impl IntegratorState {
    pub fn new(initial: f64) -> Self {
        Self {
            state: initial,
            ..Default::default()
        }
    }

    /// Propagate state using the given integration method
    pub fn propagate(&mut self, dt: f64, kpass: usize, method: IntegrationMethod) {
        match method {
            IntegrationMethod::Euler => self.euler_step(dt),
            IntegrationMethod::Rk2 => self.rk2_step(dt, kpass),
            IntegrationMethod::Rk4 => self.rk4_step(dt, kpass),
            IntegrationMethod::Merson => self.merson_step(dt, kpass),
        }
    }

    fn euler_step(&mut self, dt: f64) {
        self.state += dt * self.derivative;
    }

    fn rk2_step(&mut self, dt: f64, kpass: usize) {
        match kpass {
            0 => {
                self.x0 = self.state;
                self.xd0 = self.derivative;
                self.state = self.x0 + dt / 2.0 * self.xd0;
            }
            1 => {
                self.xd1 = self.derivative;
                self.state = self.x0 + dt * self.xd1;
            }
            _ => {}
        }
    }

    fn rk4_step(&mut self, dt: f64, kpass: usize) {
        match kpass {
            0 => {
                self.x0 = self.state;
                self.xd0 = self.derivative;
                self.state = self.x0 + dt / 2.0 * self.xd0;
            }
            1 => {
                self.xd1 = self.derivative;
                self.state = self.x0 + dt / 2.0 * self.xd1;
            }
            2 => {
                self.xd2 = self.derivative;
                self.state = self.x0 + dt * self.xd2;
            }
            3 => {
                self.xd3 = self.derivative;
                self.state = self.x0 + dt / 6.0 * (
                    self.xd0 + 2.0 * self.xd1 + 2.0 * self.xd2 + self.xd3
                );
            }
            _ => {}
        }
    }

    fn merson_step(&mut self, dt: f64, kpass: usize) {
        match kpass {
            0 => {
                self.x0 = self.state;
                self.xd0 = self.derivative;
                self.state = self.x0 + dt / 3.0 * self.xd0;
            }
            1 => {
                self.xd1 = self.derivative;
                self.state = self.x0 + dt / 6.0 * (self.xd0 + self.xd1);
            }
            2 => {
                self.xd2 = self.derivative;
                self.state = self.x0 + dt / 8.0 * (self.xd0 + 3.0 * self.xd2);
            }
            3 => {
                self.xd3 = self.derivative;
                self.state = self.x0 + dt / 2.0 * (self.xd0 - 3.0*self.xd2 + 4.0*self.xd3);
            }
            4 => {
                self.xd4 = self.derivative;
                self.state = self.x0 + dt / 6.0 * (self.xd0 + 4.0*self.xd3 + self.xd4);
            }
            _ => {}
        }
    }
}
'''
