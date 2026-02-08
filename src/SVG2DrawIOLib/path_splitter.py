"""Path splitting functionality for SVG files."""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PathSplitter:
    """Handles splitting compound SVG paths into individual subpaths."""

    def __init__(self) -> None:
        """Initialize the PathSplitter."""
        pass

    def split_svg_paths(self, input_path: Path, output_path: Path) -> dict[str, int] | None:
        """Split compound paths in an SVG file.

        Args:
            input_path: Path to input SVG file.
            output_path: Path to output SVG file.

        Returns:
            Dictionary with statistics about the split operation, or None on failure.
        """
        try:
            import svgelements
        except ImportError as e:
            logger.error("svgelements library is required for path splitting")
            raise ImportError(
                "svgelements library is required. Install with: pip install svgelements"
            ) from e

        # Parse the SVG file
        tree = ET.parse(input_path)  # nosec B314 - User-provided SVG file, user controls input
        root = tree.getroot()

        # Track statistics
        paths_processed = 0
        subpaths_created = 0
        holes_preserved = 0

        # Find all path elements
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        path_elements = root.findall(".//svg:path", namespace)

        if not path_elements:
            # Try without namespace
            path_elements = root.findall(".//path")

        logger.debug(f"Found {len(path_elements)} path element(s)")

        # Process each path
        for path_elem in path_elements:
            d_attr = path_elem.get("d")
            if not d_attr:
                continue

            # Parse with svgelements
            try:
                path = svgelements.Path(d_attr)
                subpaths = list(path.as_subpaths())

                # Only split if there are multiple subpaths
                if len(subpaths) <= 1:
                    logger.debug(f"Path has only {len(subpaths)} subpath(s), skipping")
                    continue

                logger.debug(f"Splitting path with {len(subpaths)} subpath(s)")
                paths_processed += 1

                # Group subpaths to preserve holes
                groups = self._group_paths_with_holes(subpaths)
                logger.debug(f"Created {len(groups)} path group(s)")

                # Find parent and index
                parent = self._find_parent(root, path_elem)
                if parent is None:
                    logger.warning("Could not find parent for path element")
                    continue

                index = list(parent).index(path_elem)

                # Remove original path
                parent.remove(path_elem)

                # Add grouped paths
                for group_idx, group in enumerate(groups):
                    # Create path element with proper namespace
                    new_path = ET.Element("{http://www.w3.org/2000/svg}path")

                    # Combine paths in group (for holes)
                    if len(group) > 1:
                        combined_d = " ".join(sp.d() for sp in group)
                        holes_preserved += len(group) - 1
                        logger.debug(
                            f"Group {group_idx} has {len(group)} path(s) (preserving holes)"
                        )
                    else:
                        combined_d = group[0].d()

                    new_path.set("d", combined_d)

                    # Copy attributes from original (fill, stroke, etc.)
                    # Skip 'd' and 'id' to avoid duplicates
                    for attr, value in path_elem.attrib.items():
                        if attr not in ("d", "id"):
                            new_path.set(attr, value)

                    # If original had an id, create unique ids for split paths
                    original_id = path_elem.get("id")
                    if original_id:
                        new_path.set("id", f"{original_id}-{group_idx}")

                    # Add CSS class for color control
                    existing_class = new_path.get("class", "")
                    new_class = f"{existing_class} path{group_idx}".strip()
                    new_path.set("class", new_class)

                    parent.insert(index + group_idx, new_path)
                    subpaths_created += 1

            except Exception as e:
                logger.warning(f"Failed to split path: {e}")
                continue

        # Write output with proper namespace handling
        # Register the SVG namespace to avoid ns0: prefixes
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

        return {
            "paths_processed": paths_processed,
            "subpaths_created": subpaths_created,
            "holes_preserved": holes_preserved,
        }

    def _group_paths_with_holes(self, subpaths: list[Any]) -> list[list[Any]]:
        """Group subpaths, keeping holes with their parent paths.

        Paths that are completely contained within another path are considered
        holes and are grouped with their parent.

        Args:
            subpaths: List of svgelements Path objects.

        Returns:
            List of path groups, where each group is a list of paths.
        """
        # Get bounding boxes for all subpaths
        paths_with_bbox = []
        for sp in subpaths:
            try:
                bbox = sp.bbox()
                if bbox:
                    paths_with_bbox.append((sp, bbox))
            except Exception as e:
                logger.debug(f"Could not get bbox for subpath: {e}")
                # Include path without bbox
                paths_with_bbox.append((sp, None))

        # Sort by area (largest first) - paths with no bbox go last
        def get_area(item: tuple[Any, tuple[float, float, float, float] | None]) -> float:
            _, bbox = item
            if bbox is None:
                return -1.0
            x1, y1, x2, y2 = bbox
            return (x2 - x1) * (y2 - y1)

        paths_with_bbox.sort(key=get_area, reverse=True)

        groups = []
        used = set()

        for i, (outer_path, outer_bbox) in enumerate(paths_with_bbox):
            if i in used:
                continue

            if outer_bbox is None:
                # Path without bbox - add as single group
                groups.append([outer_path])
                used.add(i)
                continue

            group = [outer_path]

            # Find all paths contained within this one
            for j, (inner_path, inner_bbox) in enumerate(paths_with_bbox):
                if (
                    j != i
                    and j not in used
                    and inner_bbox is not None
                    and self._is_path_inside_another(inner_bbox, outer_bbox)
                ):
                    group.append(inner_path)
                    used.add(j)
                    logger.debug(f"Path {j} is inside path {i} (hole detected)")

            groups.append(group)
            used.add(i)

        return groups

    def _is_path_inside_another(
        self,
        inner_bbox: tuple[float, float, float, float],
        outer_bbox: tuple[float, float, float, float],
    ) -> bool:
        """Check if inner bounding box is completely contained within outer.

        Args:
            inner_bbox: (x1, y1, x2, y2) of inner path.
            outer_bbox: (x1, y1, x2, y2) of outer path.

        Returns:
            True if inner is completely inside outer.
        """
        inner_x1, inner_y1, inner_x2, inner_y2 = inner_bbox
        outer_x1, outer_y1, outer_x2, outer_y2 = outer_bbox

        # Add small tolerance for floating point comparison
        tolerance = 0.01

        return (
            inner_x1 >= outer_x1 - tolerance
            and inner_y1 >= outer_y1 - tolerance
            and inner_x2 <= outer_x2 + tolerance
            and inner_y2 <= outer_y2 + tolerance
        )

    def _find_parent(self, root: ET.Element, target: ET.Element) -> ET.Element | None:
        """Find the parent element of a target element.

        Args:
            root: Root element to search from.
            target: Target element to find parent of.

        Returns:
            Parent element or None if not found.
        """
        for parent in root.iter():
            if target in list(parent):
                return parent
        return None
