"""C++ block templates for sink blocks."""

from ....models import BlockInfo


def template_scope(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for Scope block."""
    return f"""
// {block.name} - Scope (data recording)
class {class_name} : public Block {{
public:
    double input = 0.0;

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        output_ = input;
    }}

    double getOutput(int port = 0) const override {{
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
class {class_name} : public Block {{
public:
    double input = 0.0;

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        output_ = input;
    }}

    double getOutput(int port = 0) const override {{
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
class {class_name} : public Block {{
public:
    double input = 0.0;

    void init() override {{}}

    void update(double t) override {{
        (void)t;
    }}

    double getOutput(int port = 0) const override {{
        (void)port;
        return input;
    }}
}};
"""


def template_to_workspace(block: BlockInfo, class_name: str) -> str:
    """Generate C++ code for ToWorkspace block."""
    return f"""
// {block.name} - ToWorkspace (data logging)
class {class_name} : public Block {{
public:
    double input = 0.0;

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        output_ = input;
    }}

    double getOutput(int port = 0) const override {{
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
class {class_name} : public Block {{
public:
    double input = 0.0;   // X input
    double input1 = 0.0;  // Y input

    void init() override {{
        output_ = 0.0;
    }}

    void update(double t) override {{
        (void)t;
        output_ = input;
    }}

    double getOutput(int port = 0) const override {{
        if (port == 0) return input;
        if (port == 1) return input1;
        return input;
    }}

private:
    double output_ = 0.0;
}};
"""


SINK_TEMPLATES = {
    "scope": template_scope,
    "display": template_display,
    "terminator": template_terminator,
    "to_workspace": template_to_workspace,
    "xy_graph": template_xy_graph,
}
