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
#include <string.h>

// Get number of passes for a method (string-based for simple API)
int get_num_passes(const char* method);

// Propagate a single integrator state
// Each integrator MUST provide its own x0 storage to avoid conflicts
void propagate_integrator(
    double* state,
    double* x0, double* xd0, double* xd1, double* xd2, double* xd3,
    double derivative,
    double dt, int kpass, const char* method
);

#endif // INTEGRATION_H
'''

    @staticmethod
    def generate_c_source() -> str:
        return '''
#include "integration.h"

int get_num_passes(const char* method) {
    if (strcmp(method, "euler") == 0) return 1;
    if (strcmp(method, "rk2") == 0) return 2;
    if (strcmp(method, "rk4") == 0) return 4;
    if (strcmp(method, "merson") == 0) return 5;
    return 4;  // Default to RK4
}

void propagate_integrator(
    double* state,
    double* x0, double* xd0, double* xd1, double* xd2, double* xd3,
    double derivative,
    double dt, int kpass, const char* method
) {
    // Static storage for merson xd4 only (ok to share, just derivative)
    static double s_xd4 = 0.0;
    if (strcmp(method, "euler") == 0) {
        *state += dt * derivative;
    } else if (strcmp(method, "rk2") == 0) {
        if (kpass == 0) {
            *x0 = *state;
            *xd0 = derivative;
            *state = *x0 + dt / 2.0 * (*xd0);
        } else if (kpass == 1) {
            *xd1 = derivative;
            *state = *x0 + dt * (*xd1);
        }
    } else if (strcmp(method, "rk4") == 0) {
        if (kpass == 0) {
            *x0 = *state;
            *xd0 = derivative;
            *state = *x0 + dt / 2.0 * (*xd0);
        } else if (kpass == 1) {
            *xd1 = derivative;
            *state = *x0 + dt / 2.0 * (*xd1);
        } else if (kpass == 2) {
            *xd2 = derivative;
            *state = *x0 + dt * (*xd2);
        } else if (kpass == 3) {
            *xd3 = derivative;
            *state = *x0 + dt / 6.0 * ((*xd0) + 2.0*(*xd1) + 2.0*(*xd2) + (*xd3));
        }
    } else if (strcmp(method, "merson") == 0) {
        if (kpass == 0) {
            *x0 = *state;
            *xd0 = derivative;
            *state = *x0 + dt / 3.0 * (*xd0);
        } else if (kpass == 1) {
            *xd1 = derivative;
            *state = *x0 + dt / 6.0 * ((*xd0) + (*xd1));
        } else if (kpass == 2) {
            *xd2 = derivative;
            *state = *x0 + dt / 8.0 * ((*xd0) + 3.0 * (*xd2));
        } else if (kpass == 3) {
            *xd3 = derivative;
            *state = *x0 + dt / 2.0 * ((*xd0) - 3.0*(*xd2) + 4.0*(*xd3));
        } else if (kpass == 4) {
            s_xd4 = derivative;
            *state = *x0 + dt / 6.0 * ((*xd0) + 4.0*(*xd3) + s_xd4);
        }
    } else {
        // Default to RK4
        propagate_integrator(state, x0, xd0, xd1, xd2, xd3, derivative, dt, kpass, "rk4");
    }
}
'''

    # =========================================================================
    # C++ Integration Methods
    # =========================================================================

    @staticmethod
    def generate_cpp_header() -> str:
        return '''/**
 * Integration methods for numerical simulation.
 * Generated by LibreSim Coder.
 */

#ifndef INTEGRATION_HPP
#define INTEGRATION_HPP

#include <string>
#include <cstring>

// Get number of passes for a method
int get_num_passes(const std::string& method);

// Propagate a single integrator state
// Each integrator MUST provide its own x0 storage to avoid conflicts
void propagate_integrator(
    double& state,
    double& x0, double& xd0, double& xd1, double& xd2, double& xd3,
    double derivative,
    double dt, int kpass, const std::string& method
);

#endif // INTEGRATION_HPP
'''

    @staticmethod
    def generate_cpp_source() -> str:
        return '''/**
 * Integration methods implementation.
 * Generated by LibreSim Coder.
 */

#include "integration.hpp"

int get_num_passes(const std::string& method) {
    if (method == "euler") return 1;
    if (method == "rk2") return 2;
    if (method == "rk4") return 4;
    if (method == "merson") return 5;
    return 4;  // Default to RK4
}

static void euler_step(double& state, double derivative, double dt) {
    state += dt * derivative;
}

static void rk2_step(
    double& state, double& xd0, double& xd1,
    double derivative, double dt, int kpass, double& x0
) {
    if (kpass == 0) {
        x0 = state;
        xd0 = derivative;
        state = x0 + dt / 2.0 * xd0;
    } else if (kpass == 1) {
        xd1 = derivative;
        state = x0 + dt * xd1;
    }
}

static void rk4_step(
    double& state,
    double& xd0, double& xd1, double& xd2, double& xd3,
    double derivative, double dt, int kpass, double& x0
) {
    if (kpass == 0) {
        x0 = state;
        xd0 = derivative;
        state = x0 + dt / 2.0 * xd0;
    } else if (kpass == 1) {
        xd1 = derivative;
        state = x0 + dt / 2.0 * xd1;
    } else if (kpass == 2) {
        xd2 = derivative;
        state = x0 + dt * xd2;
    } else if (kpass == 3) {
        xd3 = derivative;
        state = x0 + dt / 6.0 * (xd0 + 2.0*xd1 + 2.0*xd2 + xd3);
    }
}

static void merson_step(
    double& state,
    double& xd0, double& xd1, double& xd2, double& xd3,
    double derivative, double dt, int kpass, double& x0, double& xd4
) {
    if (kpass == 0) {
        x0 = state;
        xd0 = derivative;
        state = x0 + dt / 3.0 * xd0;
    } else if (kpass == 1) {
        xd1 = derivative;
        state = x0 + dt / 6.0 * (xd0 + xd1);
    } else if (kpass == 2) {
        xd2 = derivative;
        state = x0 + dt / 8.0 * (xd0 + 3.0 * xd2);
    } else if (kpass == 3) {
        xd3 = derivative;
        state = x0 + dt / 2.0 * (xd0 - 3.0*xd2 + 4.0*xd3);
    } else if (kpass == 4) {
        xd4 = derivative;
        state = x0 + dt / 6.0 * (xd0 + 4.0*xd3 + xd4);
    }
}

// Static storage for merson xd4 (rarely used, ok to share)
static double s_xd4 = 0.0;

void propagate_integrator(
    double& state,
    double& x0, double& xd0, double& xd1, double& xd2, double& xd3,
    double derivative,
    double dt, int kpass, const std::string& method
) {
    if (method == "euler") {
        euler_step(state, derivative, dt);
    } else if (method == "rk2") {
        rk2_step(state, xd0, xd1, derivative, dt, kpass, x0);
    } else if (method == "rk4") {
        rk4_step(state, xd0, xd1, xd2, xd3, derivative, dt, kpass, x0);
    } else if (method == "merson") {
        merson_step(state, xd0, xd1, xd2, xd3, derivative, dt, kpass, x0, s_xd4);
    } else {
        // Default to RK4
        rk4_step(state, xd0, xd1, xd2, xd3, derivative, dt, kpass, x0);
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

    /// Parse from string
    pub fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "euler" => IntegrationMethod::Euler,
            "rk2" => IntegrationMethod::Rk2,
            "rk4" => IntegrationMethod::Rk4,
            "merson" => IntegrationMethod::Merson,
            _ => IntegrationMethod::Rk4,  // Default
        }
    }
}

/// Get number of passes for an integration method
pub fn get_num_passes(method: IntegrationMethod) -> usize {
    method.passes()
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

/// Propagate a single integrator state
/// Each integrator MUST provide its own x0 storage to avoid conflicts
pub fn propagate_integrator(
    state: &mut f64,
    x0: &mut f64,
    xd0: &mut f64,
    xd1: &mut f64,
    xd2: &mut f64,
    xd3: &mut f64,
    derivative: f64,
    dt: f64,
    kpass: usize,
    method: IntegrationMethod,
) {
    match method {
        IntegrationMethod::Euler => {
            *state += dt * derivative;
        }
        IntegrationMethod::Rk2 => {
            match kpass {
                0 => {
                    *x0 = *state;
                    *xd0 = derivative;
                    *state = *x0 + dt / 2.0 * *xd0;
                }
                1 => {
                    *xd1 = derivative;
                    *state = *x0 + dt * *xd1;
                }
                _ => {}
            }
        }
        IntegrationMethod::Rk4 => {
            match kpass {
                0 => {
                    *x0 = *state;
                    *xd0 = derivative;
                    *state = *x0 + dt / 2.0 * *xd0;
                }
                1 => {
                    *xd1 = derivative;
                    *state = *x0 + dt / 2.0 * *xd1;
                }
                2 => {
                    *xd2 = derivative;
                    *state = *x0 + dt * *xd2;
                }
                3 => {
                    *xd3 = derivative;
                    *state = *x0 + dt / 6.0 * (*xd0 + 2.0 * *xd1 + 2.0 * *xd2 + *xd3);
                }
                _ => {}
            }
        }
        IntegrationMethod::Merson => {
            // Static storage for xd4 only (ok to share, just derivative)
            thread_local! {
                static XD4: std::cell::RefCell<f64> = std::cell::RefCell::new(0.0);
            }
            XD4.with(|xd4_cell| {
                let mut xd4 = xd4_cell.borrow_mut();
                match kpass {
                    0 => {
                        *x0 = *state;
                        *xd0 = derivative;
                        *state = *x0 + dt / 3.0 * *xd0;
                    }
                    1 => {
                        *xd1 = derivative;
                        *state = *x0 + dt / 6.0 * (*xd0 + *xd1);
                    }
                    2 => {
                        *xd2 = derivative;
                        *state = *x0 + dt / 8.0 * (*xd0 + 3.0 * *xd2);
                    }
                    3 => {
                        *xd3 = derivative;
                        *state = *x0 + dt / 2.0 * (*xd0 - 3.0 * *xd2 + 4.0 * *xd3);
                    }
                    4 => {
                        *xd4 = derivative;
                        *state = *x0 + dt / 6.0 * (*xd0 + 4.0 * *xd3 + *xd4);
                    }
                    _ => {}
                }
            });
        }
    }
}
'''
