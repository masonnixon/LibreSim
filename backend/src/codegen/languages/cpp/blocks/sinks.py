"""C++ block templates for sink blocks."""

from ....models import BlockInfo


def template_scope(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Scope block."""
    num_inputs = block.parameters.get("numInputs", 1)

    if num_inputs > 1:
        # Generate input members: input (port 0), input1 (port 1), input2 (port 2), etc.
        input_members = ["double input = 0.0;"]
        for i in range(1, num_inputs):
            input_members.append(f"double input{i} = 0.0;")
        input_members_str = "\n    ".join(input_members)

        # Generate outputs array initialization
        outputs_init = ", ".join(["0.0"] * num_inputs)

        # Generate get_output switch
        get_output_cases = ["if (port == 0) return outputs_[0];"]
        for i in range(1, num_inputs):
            get_output_cases.append(f"if (port == {i}) return outputs_[{i}];")
        get_output_str = "\n        ".join(get_output_cases)

        # Generate update code
        update_lines = ["outputs_[0] = input;"]
        for i in range(1, num_inputs):
            update_lines.append(f"outputs_[{i}] = input{i};")
        update_str = "\n        ".join(update_lines)

        return f"""
// {block.name} - Scope (data recording, {num_inputs} inputs)
class {class_name} {{
public:
    {input_members_str}

    void init() {{
        for (int i = 0; i < {num_inputs}; ++i) outputs_[i] = 0.0;
    }}

    void update(double t) {{
        (void)t;
        {update_str}
    }}

    double get_output(int port = 0) const {{
        {get_output_str}
        return 0.0;
    }}

private:
    double outputs_[{num_inputs}] = {{{outputs_init}}};
}};
"""
    else:
        return f"""
// {block.name} - Scope (data recording)
class {class_name} {{
public:
    double input = 0.0;

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = input;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_display(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Display block."""
    return f"""
// {block.name} - Display
class {class_name} {{
public:
    double input = 0.0;

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = input;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_terminator(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Terminator block."""
    return f"""
// {block.name} - Terminator (absorbs signal)
class {class_name} {{
public:
    double input = 0.0;

    void init() {{}}

    void update(double t) {{
        (void)t;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return input;
    }}
}};
"""


def template_to_workspace(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for ToWorkspace block."""
    return f"""
// {block.name} - ToWorkspace (data logging)
class {class_name} {{
public:
    double input = 0.0;

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = input;
    }}

    double get_output(int port = 0) const {{
        (void)port;
        return output_;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_xy_graph(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for XY Graph block."""
    return f"""
// {block.name} - XY Graph
class {class_name} {{
public:
    double input = 0.0;   // X input
    double input1 = 0.0;  // Y input

    void init() {{
        output_ = 0.0;
    }}

    void update(double t) {{
        (void)t;
        output_ = input;
    }}

    double get_output(int port = 0) const {{
        if (port == 0) return input;
        if (port == 1) return input1;
        return input;
    }}

private:
    double output_ = 0.0;
}};
"""


def template_scope_3d(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for 3D Scope block."""
    return f"""
// {block.name} - 3D Scope
class {class_name} {{
public:
    double input = 0.0;   // X input
    double input1 = 0.0;  // Y input
    double input2 = 0.0;  // Z input

    void init() {{
    }}

    void update(double t) {{
        (void)t;
    }}

    double get_output(int port = 0) const {{
        if (port == 0) return input;
        if (port == 1) return input1;
        if (port == 2) return input2;
        return input;
    }}
}};
"""


SINK_TEMPLATES = {
    "scope": template_scope,
    "display": template_display,
    "terminator": template_terminator,
    "to_workspace": template_to_workspace,
    "xy_graph": template_xy_graph,
    "scope_3d": template_scope_3d,
}
