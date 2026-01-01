"""C block templates for sink blocks."""

from ....models import BlockInfo


def template_scope(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Scope block."""
    return f"""
// {block.name} - Scope (data recording)
typedef struct {{
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = b->input;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_display(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Display block."""
    return f"""
// {block.name} - Display
typedef struct {{
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = b->input;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_terminator(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Terminator block."""
    return f"""
// {block.name} - Terminator (absorbs signal)
typedef struct {{
    double input;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    (void)b;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->input;
}}
"""


def template_to_workspace(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for ToWorkspace block."""
    return f"""
// {block.name} - ToWorkspace (data logging)
typedef struct {{
    double input;
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    b->output = b->input;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    (void)port;
    return b->output;
}}
"""


def template_xy_graph(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for XY Graph block."""
    return f"""
// {block.name} - XY Graph
typedef struct {{
    double input;   // X input
    double input1;  // Y input
    double output;
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    b->input = 0.0;
    b->input1 = 0.0;
    b->output = 0.0;
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    // XY Graph just records data, output is X value
    b->output = b->input;
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    if (port == 0) return b->input;
    if (port == 1) return b->input1;
    return b->input;
}}
"""


SINK_TEMPLATES = {
    "scope": template_scope,
    "display": template_display,
    "terminator": template_terminator,
    "to_workspace": template_to_workspace,
    "xy_graph": template_xy_graph,
}
