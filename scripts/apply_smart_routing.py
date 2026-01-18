#!/usr/bin/env python3
"""
Apply smart routing to all LibreSim example files.

This script regenerates waypoints for connections that would cross over blocks,
similar to the smart auto-routing implemented in the frontend.
"""

import json
from pathlib import Path


# Default block dimensions (same as frontend)
DEFAULT_BLOCK_WIDTH = 80
DEFAULT_BLOCK_HEIGHT = 50
ROUTING_MARGIN = 15  # Margin around blocks


def get_block_bounds(block: dict, margin: float = ROUTING_MARGIN) -> dict:
    """Get bounding box of a block with optional margin."""
    pos = block["position"]
    size = block.get("size", {"width": DEFAULT_BLOCK_WIDTH, "height": DEFAULT_BLOCK_HEIGHT})
    width = size.get("width", DEFAULT_BLOCK_WIDTH)
    height = size.get("height", DEFAULT_BLOCK_HEIGHT)

    return {
        "left": pos["x"] - margin,
        "right": pos["x"] + width + margin,
        "top": pos["y"] - margin,
        "bottom": pos["y"] + height + margin,
        "centerY": pos["y"] + height / 2,
    }


def get_port_position(block: dict, port_id: str, is_output: bool) -> dict:
    """Get the position of a port on a block."""
    pos = block["position"]
    size = block.get("size", {"width": DEFAULT_BLOCK_WIDTH, "height": DEFAULT_BLOCK_HEIGHT})
    width = size.get("width", DEFAULT_BLOCK_WIDTH)
    height = size.get("height", DEFAULT_BLOCK_HEIGHT)

    # Find port index
    ports = block["outputPorts"] if is_output else block["inputPorts"]
    port_index = 0
    for i, p in enumerate(ports):
        if p["id"] == port_id:
            port_index = i
            break

    num_ports = len(ports)
    # Distribute ports evenly along the height
    port_spacing = height / (num_ports + 1)
    port_y = pos["y"] + port_spacing * (port_index + 1)

    if is_output:
        return {"x": pos["x"] + width, "y": port_y}
    else:
        return {"x": pos["x"], "y": port_y}


def line_intersects_rect(x1: float, y1: float, x2: float, y2: float, rect: dict) -> bool:
    """Check if a line segment intersects a rectangle."""
    # Check if line is completely to one side of the rect
    if max(x1, x2) < rect["left"] or min(x1, x2) > rect["right"]:
        return False
    if max(y1, y2) < rect["top"] or min(y1, y2) > rect["bottom"]:
        return False

    # For horizontal lines
    if abs(y1 - y2) < 0.001:
        return rect["top"] <= y1 <= rect["bottom"]

    # For vertical lines
    if abs(x1 - x2) < 0.001:
        return rect["left"] <= x1 <= rect["right"]

    # For diagonal lines (though we use orthogonal routing, this handles edge cases)
    return True


def segment_intersects_block(
    x1: float, y1: float, x2: float, y2: float,
    block: dict, exclude_block_ids: set, margin: float = ROUTING_MARGIN
) -> bool:
    """Check if a line segment intersects a block (excluding source/target blocks)."""
    if block["id"] in exclude_block_ids:
        return False

    bounds = get_block_bounds(block, margin)
    return line_intersects_rect(x1, y1, x2, y2, bounds)


def generate_smart_waypoints(
    source_pos: dict, target_pos: dict,
    source_block_id: str, target_block_id: str,
    all_blocks: list, margin: float = ROUTING_MARGIN
) -> list:
    """
    Generate waypoints for a connection that avoids crossing blocks.
    Returns a list of waypoint coordinates.

    Routing preferences (based on user's PID Controller example):
    - Feedback loops (backwards connections): Route BELOW all blocks
    - Forward connections crossing blocks: Route ABOVE the blocking blocks
    """
    sx, sy = source_pos["x"], source_pos["y"]
    tx, ty = target_pos["x"], target_pos["y"]

    exclude_ids = {source_block_id, target_block_id}

    # Check if direct horizontal-then-vertical path would intersect any blocks
    mid_x = (sx + tx) / 2

    has_collision = False
    for block in all_blocks:
        if segment_intersects_block(sx, sy, mid_x, sy, block, exclude_ids, margin):
            has_collision = True
            break
        if segment_intersects_block(mid_x, sy, mid_x, ty, block, exclude_ids, margin):
            has_collision = True
            break
        if segment_intersects_block(mid_x, ty, tx, ty, block, exclude_ids, margin):
            has_collision = True
            break

    if not has_collision and tx > sx:
        # Direct path is fine for forward connections
        return []

    # For backwards connections or collisions, generate smart waypoints
    blocking_blocks = []
    for block in all_blocks:
        if block["id"] in exclude_ids:
            continue
        bounds = get_block_bounds(block, margin)
        # Check if block is between source and target
        if min(sx, tx) < bounds["right"] and max(sx, tx) > bounds["left"]:
            if min(sy, ty) - margin < bounds["bottom"] and max(sy, ty) + margin > bounds["top"]:
                blocking_blocks.append(block)

    if not blocking_blocks and tx > sx:
        return []

    # Get all block bounds for collision checking
    all_bounds = [get_block_bounds(b, margin) for b in all_blocks if b["id"] not in exclude_ids]

    # Determine routing strategy based on connection direction
    if tx < sx:
        # Backwards connection (feedback loop) - ALWAYS route BELOW all blocks
        # This matches Simulink convention for feedback loops

        if not all_bounds:
            # No other blocks, simple U-route below
            route_y = max(sy, ty) + 60
            return [
                {"x": sx + 20, "y": route_y},
                {"x": tx - 20, "y": route_y},
            ]

        # Find max bottom of all blocks in the path
        max_bottom = max(b["bottom"] for b in all_bounds)

        # Route below all blocks with margin
        route_y = max_bottom + margin + 10

        # Find X positions for waypoints that don't cross blocks vertically
        # Start with offsets from source and target
        wp1_x = sx + 20
        wp2_x = tx - 20

        # Check if vertical segment at wp1_x crosses any block
        for block in all_blocks:
            if vertical_line_crosses_block(wp1_x, sy, route_y, block, exclude_ids, margin):
                # Move waypoint X to the right of the blocking block
                bounds = get_block_bounds(block, margin)
                wp1_x = bounds["right"] + 5

        # Check if vertical segment at wp2_x crosses any block
        for block in all_blocks:
            if vertical_line_crosses_block(wp2_x, ty, route_y, block, exclude_ids, margin):
                # Move waypoint X to the left of the blocking block
                bounds = get_block_bounds(block, margin)
                wp2_x = bounds["left"] - 5

        return [
            {"x": wp1_x, "y": route_y},
            {"x": wp2_x, "y": route_y},
        ]

    # Forward connection with blocking blocks - route ABOVE
    if blocking_blocks:
        blocking_bounds = [get_block_bounds(b, margin) for b in blocking_blocks]
        min_top = min(b["top"] for b in blocking_bounds)

        # Route above blocking blocks
        route_y = min_top - margin - 10

        # Find a good X for the waypoint that doesn't cause vertical segment collisions
        mid_x = (sx + tx) / 2

        # Check if vertical segments at mid_x cross any blocks
        needs_adjustment = False
        for block in all_blocks:
            if vertical_line_crosses_block(mid_x, sy, route_y, block, exclude_ids, margin):
                needs_adjustment = True
                break
            if vertical_line_crosses_block(mid_x, route_y, ty, block, exclude_ids, margin):
                needs_adjustment = True
                break

        if needs_adjustment:
            # Use two waypoints to route around blocks
            # Find clear X positions
            wp1_x = sx + 20
            wp2_x = tx - 20

            # Adjust wp1_x if it crosses a block
            for block in all_blocks:
                if vertical_line_crosses_block(wp1_x, sy, route_y, block, exclude_ids, margin):
                    bounds = get_block_bounds(block, margin)
                    wp1_x = bounds["right"] + 5

            # Adjust wp2_x if it crosses a block
            for block in all_blocks:
                if vertical_line_crosses_block(wp2_x, route_y, ty, block, exclude_ids, margin):
                    bounds = get_block_bounds(block, margin)
                    wp2_x = bounds["left"] - 5

            return [
                {"x": wp1_x, "y": route_y},
                {"x": wp2_x, "y": route_y},
            ]

        return [
            {"x": mid_x, "y": route_y},
        ]

    return []


def horizontal_line_crosses_block(
    x1: float, x2: float, y: float,
    block: dict, exclude_block_ids: set, margin: float = ROUTING_MARGIN
) -> bool:
    """Check if a horizontal line at y from x1 to x2 crosses through a block."""
    if block["id"] in exclude_block_ids:
        return False

    bounds = get_block_bounds(block, margin)

    # Line must be within vertical extent of block
    if y < bounds["top"] or y > bounds["bottom"]:
        return False

    # Line must overlap horizontally with block
    line_left = min(x1, x2)
    line_right = max(x1, x2)

    # Check if x-ranges overlap
    return not (line_right < bounds["left"] or line_left > bounds["right"])


def vertical_line_crosses_block(
    x: float, y1: float, y2: float,
    block: dict, exclude_block_ids: set, margin: float = ROUTING_MARGIN
) -> bool:
    """Check if a vertical line at x from y1 to y2 crosses through a block."""
    if block["id"] in exclude_block_ids:
        return False

    bounds = get_block_bounds(block, margin)

    # Line must be within horizontal extent of block
    if x < bounds["left"] or x > bounds["right"]:
        return False

    # Line must overlap vertically with block
    line_top = min(y1, y2)
    line_bottom = max(y1, y2)

    # Check if y-ranges overlap
    return not (line_bottom < bounds["top"] or line_top > bounds["bottom"])


def route_crosses_any_block(
    source_pos: dict, target_pos: dict, waypoints: list,
    blocks: list, exclude_block_ids: set, margin: float = ROUTING_MARGIN
) -> bool:
    """
    Check if the complete route (including all segments) crosses any blocks.
    The route goes: source → waypoint1 → waypoint2 → ... → target
    With orthogonal routing between each point (horizontal then vertical).
    """
    # Build the path: source -> waypoints -> target
    path_points = [source_pos] + waypoints + [target_pos]

    for i in range(len(path_points) - 1):
        p1 = path_points[i]
        p2 = path_points[i + 1]

        # Orthogonal path: horizontal first, then vertical
        # Segment 1: horizontal from p1.x to p2.x at p1.y
        for block in blocks:
            if horizontal_line_crosses_block(p1["x"], p2["x"], p1["y"], block, exclude_block_ids, margin):
                return True

        # Segment 2: vertical from p1.y to p2.y at p2.x
        for block in blocks:
            if vertical_line_crosses_block(p2["x"], p1["y"], p2["y"], block, exclude_block_ids, margin):
                return True

    return False


def process_model(model: dict) -> tuple[dict, int]:
    """Process a model and add smart waypoints to connections.
    Returns the updated model and count of connections with new waypoints.

    Handles overlapping lines by tracking used Y coordinates and offsetting
    subsequent connections to prevent overlaps. Each connection gets a unique
    routing channel, but all waypoints within a single connection share the
    same Y coordinate.

    Also ensures routes don't go through blocks by checking block collisions
    when adjusting Y levels.
    """
    blocks = model.get("blocks", [])
    connections = model.get("connections", [])

    block_map = {b["id"]: b for b in blocks}

    waypoints_added = 0

    # Track used Y coordinates to prevent overlapping lines
    # Key: rounded Y coordinate, Value: list of x-ranges using it
    used_routing_levels: dict[int, list[tuple[float, float]]] = {}
    LINE_SPACING = 20  # Minimum spacing between parallel lines

    # First pass: generate initial waypoints
    connection_waypoints: list[tuple[dict, list, dict, dict, str, str]] = []

    for conn in connections:
        source_block = block_map.get(conn["sourceBlockId"])
        target_block = block_map.get(conn["targetBlockId"])

        if not source_block or not target_block:
            connection_waypoints.append((conn, [], {}, {}, "", ""))
            continue

        source_pos = get_port_position(source_block, conn["sourcePortId"], is_output=True)
        target_pos = get_port_position(target_block, conn["targetPortId"], is_output=False)

        waypoints = generate_smart_waypoints(
            source_pos, target_pos,
            conn["sourceBlockId"], conn["targetBlockId"],
            blocks
        )

        connection_waypoints.append((
            conn, waypoints, source_pos, target_pos,
            conn["sourceBlockId"], conn["targetBlockId"]
        ))

    # Second pass: resolve overlaps by offsetting Y coordinates
    for conn, waypoints, source_pos, target_pos, src_id, tgt_id in connection_waypoints:
        if not waypoints:
            if "waypoints" in conn:
                del conn["waypoints"]
            continue

        # Get the base routing Y (all waypoints in a feedback loop share the same Y)
        base_y = waypoints[0]["y"]
        rounded_y = round(base_y / LINE_SPACING) * LINE_SPACING

        # Calculate the x-range this connection spans
        all_x = [wp["x"] for wp in waypoints]
        if source_pos:
            all_x.append(source_pos["x"])
        if target_pos:
            all_x.append(target_pos["x"])
        x_min, x_max = min(all_x), max(all_x)

        exclude_ids = {src_id, tgt_id}

        # Check if this routing level overlaps with existing connections
        def has_line_overlap(y_level: int) -> bool:
            if y_level not in used_routing_levels:
                return False
            for existing_min, existing_max in used_routing_levels[y_level]:
                # Check if x-ranges overlap
                if not (x_max < existing_min - 10 or x_min > existing_max + 10):
                    return True
            return False

        # Check if routing at this Y level would cross any blocks
        # We need to check both horizontal and vertical segments
        def crosses_block(y_level: int) -> bool:
            # Check horizontal segment at the routing level
            for block in blocks:
                if horizontal_line_crosses_block(x_min, x_max, y_level, block, exclude_ids):
                    return True

            # Also check vertical segments from source/target to the routing level
            if source_pos:
                for block in blocks:
                    # Check vertical from source Y to routing Y at the first waypoint X
                    wp_x = waypoints[0]["x"] if waypoints else x_min
                    if vertical_line_crosses_block(wp_x, source_pos["y"], y_level, block, exclude_ids):
                        return True

            if target_pos:
                for block in blocks:
                    # Check vertical from routing Y to target Y at the last waypoint X
                    wp_x = waypoints[-1]["x"] if waypoints else x_max
                    if vertical_line_crosses_block(wp_x, y_level, target_pos["y"], block, exclude_ids):
                        return True

            return False

        # Determine direction to search for free Y level
        # For feedback loops (routing below), search downward
        # For forward connections (routing above), search upward
        is_feedback = target_pos and source_pos and target_pos["x"] < source_pos["x"]

        # Find a Y level without overlap AND without crossing blocks
        max_iterations = 50  # Prevent infinite loop
        iterations = 0
        while (has_line_overlap(rounded_y) or crosses_block(rounded_y)) and iterations < max_iterations:
            if is_feedback:
                rounded_y += LINE_SPACING  # Go further down for feedback
            else:
                rounded_y -= LINE_SPACING  # Go further up for forward connections
            iterations += 1

        # If we couldn't find a good level going one direction, try the other
        if iterations >= max_iterations:
            rounded_y = round(base_y / LINE_SPACING) * LINE_SPACING
            iterations = 0
            while (has_line_overlap(rounded_y) or crosses_block(rounded_y)) and iterations < max_iterations:
                if is_feedback:
                    rounded_y -= LINE_SPACING
                else:
                    rounded_y += LINE_SPACING
                iterations += 1

        # Mark this Y level as used with its x-range
        if rounded_y not in used_routing_levels:
            used_routing_levels[rounded_y] = []
        used_routing_levels[rounded_y].append((x_min, x_max))

        # Apply the same Y to all waypoints in this connection
        adjusted_waypoints = [{"x": wp["x"], "y": rounded_y} for wp in waypoints]

        conn["waypoints"] = adjusted_waypoints
        waypoints_added += 1

    return model, waypoints_added


def main():
    examples_dir = Path(__file__).parent.parent / "examples"

    json_files = sorted(examples_dir.glob("*.json"))

    print(f"Found {len(json_files)} example files")

    total_waypoints = 0
    for json_file in json_files:
        with open(json_file, encoding="utf-8") as f:
            model = json.load(f)

        updated_model, waypoints_added = process_model(model)

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(updated_model, f, indent=2)
            f.write("\n")

        status = f"  ({waypoints_added} connections routed)" if waypoints_added else ""
        print(f"  {json_file.name}{status}")
        total_waypoints += waypoints_added

    print(f"\nApplied smart routing to {total_waypoints} connections across all files")


if __name__ == "__main__":
    main()
