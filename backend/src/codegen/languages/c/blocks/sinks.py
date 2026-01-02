"""C block templates for sink blocks."""

from ....models import BlockInfo


def template_scope(block: BlockInfo, struct_name: str) -> str:
    """Generate C code for Scope block."""
    num_inputs = block.parameters.get("numInputs", 1)

    if num_inputs > 1:
        # Generate input members: input (port 0), input1 (port 1), input2 (port 2), etc.
        input_members = ["double input;"]
        for i in range(1, num_inputs):
            input_members.append(f"double input{i};")
        input_members_str = "\n    ".join(input_members)

        # Generate init code
        init_lines = ["b->input = 0.0;"]
        for i in range(1, num_inputs):
            init_lines.append(f"b->input{i} = 0.0;")
        init_lines.append("for (int i = 0; i < " + str(num_inputs) + "; ++i) b->outputs[i] = 0.0;")
        init_str = "\n    ".join(init_lines)

        # Generate update code
        update_lines = ["b->outputs[0] = b->input;"]
        for i in range(1, num_inputs):
            update_lines.append(f"b->outputs[{i}] = b->input{i};")
        update_str = "\n    ".join(update_lines)

        # Generate get_output code
        get_output_cases = ["if (port == 0) return b->outputs[0];"]
        for i in range(1, num_inputs):
            get_output_cases.append(f"if (port == {i}) return b->outputs[{i}];")
        get_output_str = "\n    ".join(get_output_cases)

        return f"""
// {block.name} - Scope (data recording, {num_inputs} inputs)
typedef struct {{
    {input_members_str}
    double outputs[{num_inputs}];
}} {struct_name};

void {struct_name}_init({struct_name}* b) {{
    {init_str}
}}

void {struct_name}_update({struct_name}* b, double t) {{
    (void)t;
    {update_str}
}}

double {struct_name}_get_output({struct_name}* b, int port) {{
    {get_output_str}
    return 0.0;
}}
"""
    else:
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
