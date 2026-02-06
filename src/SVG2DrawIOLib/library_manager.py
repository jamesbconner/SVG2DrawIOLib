"""DrawIO library management functionality."""

import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

from SVG2DrawIOLib.models import DrawIOIcon, LibraryMetadata

logger = logging.getLogger(__name__)


class LibraryManager:
    """Manages DrawIO library files."""

    def __init__(self) -> None:
        """Initialize the library manager."""
        pass

    def create_library(self, icons: list[DrawIOIcon], output_path: Path) -> LibraryMetadata:
        """Create a new DrawIO library from icons.

        Args:
            icons: List of DrawIO icons to include.
            output_path: Path where the library file will be saved.

        Returns:
            LibraryMetadata with information about the created library.
        """
        logger.info(f"Creating library with {len(icons)} icon(s)")

        # Sort icons alphabetically by name
        sorted_icons = sorted(icons, key=lambda icon: icon.name)

        # Convert to library JSON format
        library_data = [icon.to_dict() for icon in sorted_icons]
        library_json = json.dumps(library_data)

        # Create XML structure
        mxlibrary = ET.Element("mxlibrary")
        mxlibrary.text = library_json

        tree = ET.ElementTree(mxlibrary)

        # Write to file
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

        logger.info(f"Library created successfully: {output_path}")

        return LibraryMetadata(
            name=output_path.stem,
            icon_count=len(icons),
            source_files=[],
        )

    def load_library(self, library_path: Path) -> list[DrawIOIcon]:
        """Load icons from an existing DrawIO library.

        Args:
            library_path: Path to the library file.

        Returns:
            List of DrawIO icons from the library.

        Raises:
            FileNotFoundError: If the library file does not exist.
            ValueError: If the library file is invalid.
        """
        if not library_path.exists():
            logger.error(f"Library file not found: {library_path}")
            raise FileNotFoundError(f"Library file not found: {library_path}")

        logger.debug(f"Loading library: {library_path}")

        try:
            tree = ET.parse(library_path)  # nosec B314 - User-provided library file, user controls input
            root = tree.getroot()

            if root.tag != "mxlibrary":
                raise ValueError(
                    f"Invalid library file: root element is {root.tag}, expected mxlibrary"
                )

            if not root.text:
                logger.warning("Library file is empty")
                return []

            library_data = json.loads(root.text)

            icons = []
            for item in library_data:
                # Convert from library format back to DrawIOIcon
                # Note: We need to re-encode the XML data
                from SVG2DrawIOLib.models import SVGDimensions

                icon = DrawIOIcon(
                    name=item["title"],
                    xml_data=item["xml"].encode("ascii"),
                    dimensions=SVGDimensions(width=item["w"], height=item["h"]),
                )
                icons.append(icon)

            logger.info(f"Loaded {len(icons)} icon(s) from library")
            return icons

        except ET.ParseError as e:
            logger.error(f"Failed to parse library file: {e}")
            raise ValueError(f"Invalid library file: {e}") from e
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Invalid library format: {e}")
            raise ValueError(f"Invalid library format: {e}") from e

    def add_icons_to_library(
        self,
        library_path: Path,
        new_icons: list[DrawIOIcon],
        replace_duplicates: bool = False,
        add_duplicates: bool = False,
    ) -> LibraryMetadata:
        """Add icons to an existing library.

        Args:
            library_path: Path to the existing library file.
            new_icons: List of icons to add.
            replace_duplicates: If True, replace icons with duplicate names.
            add_duplicates: If True, add duplicates with modified names (e.g., icon_2, icon_3).

        Returns:
            LibraryMetadata with updated library information.

        Raises:
            FileNotFoundError: If the library file does not exist.
            ValueError: If the library file is invalid.
        """
        logger.info(f"Adding {len(new_icons)} icon(s) to library: {library_path}")

        # Load existing icons
        existing_icons = self.load_library(library_path)

        # Check for duplicate names in existing icons and warn
        existing_names = [icon.name for icon in existing_icons]
        if len(existing_names) != len(set(existing_names)):
            # Find duplicates
            seen = set()
            duplicates = set()
            for name in existing_names:
                if name in seen:
                    duplicates.add(name)
                seen.add(name)

            logger.warning(
                f"Library contains {len(duplicates)} icon(s) with duplicate names: {sorted(duplicates)}. "
                "Only the last occurrence of each duplicate will be preserved."
            )

        # Create a map of existing icons by name (last occurrence wins)
        icon_map = {icon.name: icon for icon in existing_icons}

        # Add or replace icons
        added_count = 0
        replaced_count = 0
        skipped_count = 0

        for new_icon in new_icons:
            if new_icon.name in icon_map:
                if replace_duplicates:
                    icon_map[new_icon.name] = new_icon
                    replaced_count += 1
                    logger.debug(f"Replaced icon: {new_icon.name}")
                elif add_duplicates:
                    # Find a unique name by appending _2, _3, etc.
                    base_name = new_icon.name
                    counter = 2
                    unique_name = f"{base_name}_{counter}"
                    while unique_name in icon_map:
                        counter += 1
                        unique_name = f"{base_name}_{counter}"

                    # Create new icon with unique name
                    unique_icon = DrawIOIcon(
                        name=unique_name,
                        xml_data=new_icon.xml_data,
                        dimensions=new_icon.dimensions,
                    )
                    icon_map[unique_name] = unique_icon
                    added_count += 1
                    logger.debug(f"Added duplicate icon with modified name: {unique_name}")
                else:
                    skipped_count += 1
                    logger.debug(f"Skipped duplicate icon: {new_icon.name}")
            else:
                icon_map[new_icon.name] = new_icon
                added_count += 1
                logger.debug(f"Added icon: {new_icon.name}")

        logger.info(f"Added: {added_count}, Replaced: {replaced_count}, Skipped: {skipped_count}")

        # Save updated library
        all_icons = list(icon_map.values())
        return self.create_library(all_icons, library_path)

    def remove_icons_from_library(
        self, library_path: Path, icon_names: list[str]
    ) -> tuple[LibraryMetadata, int]:
        """Remove icons from a library by name.

        Args:
            library_path: Path to the library file.
            icon_names: List of icon names to remove.

        Returns:
            Tuple of (LibraryMetadata with updated library information, number of icons actually removed).

        Raises:
            FileNotFoundError: If the library file does not exist.
            ValueError: If the library file is invalid.
        """
        logger.info(f"Removing {len(icon_names)} icon(s) from library: {library_path}")

        # Load existing icons
        existing_icons = self.load_library(library_path)

        # Filter out icons to remove
        names_to_remove = set(icon_names)
        filtered_icons = [icon for icon in existing_icons if icon.name not in names_to_remove]

        removed_count = len(existing_icons) - len(filtered_icons)
        logger.info(f"Removed {removed_count} icon(s)")

        # Save updated library
        metadata = self.create_library(filtered_icons, library_path)
        return metadata, removed_count

    def list_icons(self, library_path: Path) -> list[str]:
        """List all icon names in a library.

        Args:
            library_path: Path to the library file.

        Returns:
            List of icon names.

        Raises:
            FileNotFoundError: If the library file does not exist.
            ValueError: If the library file is invalid.
        """
        icons = self.load_library(library_path)
        return [icon.name for icon in icons]
