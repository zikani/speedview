import argparse
import hashlib
import os
import uuid
import xml.etree.ElementTree as ET


WIX_NS = "http://wixtoolset.org/schemas/v4/wxs"
UUID_NAMESPACE = uuid.UUID("7E19C4A1-8E65-4D1B-A2E7-5F9E0A44B210")


def _safe_id(prefix, rel_path):
    digest = hashlib.sha1(rel_path.replace("\\", "/").encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def generate_app_files_wxs(dist_dir, output_path):
    """Generate a WiX v4 compatible AppFiles.wxs harvesting every file & subdir in dist_dir."""
    dist_abs = os.path.abspath(dist_dir)
    if not os.path.isdir(dist_abs):
        raise FileNotFoundError(f"Onedir distribution directory not found: {dist_abs}")

    ET.register_namespace("", WIX_NS)
    wix_el = ET.Element(f"{{{WIX_NS}}}Wix")

    dir_frag = ET.SubElement(wix_el, f"{{{WIX_NS}}}Fragment")
    dir_ref = ET.SubElement(dir_frag, f"{{{WIX_NS}}}DirectoryRef", {"Id": "INSTALLFOLDER"})

    comp_frag = ET.SubElement(wix_el, f"{{{WIX_NS}}}Fragment")
    comp_group = ET.SubElement(comp_frag, f"{{{WIX_NS}}}ComponentGroup", {"Id": "AppFiles"})

    dir_ids = {".": "INSTALLFOLDER"}
    dir_elements = {".": dir_ref}

    for root, dirs, files in sorted(os.walk(dist_abs)):
        dirs.sort()
        files.sort()
        rel_dir = os.path.relpath(root, dist_abs)
        rel_norm = "." if rel_dir == "." else rel_dir.replace("\\", "/")

        if rel_norm != ".":
            parent_rel = os.path.dirname(rel_norm) or "."
            parent_el = dir_elements[parent_rel]
            dir_id = _safe_id("Dir", rel_norm)
            dir_el = ET.SubElement(
                parent_el,
                f"{{{WIX_NS}}}Directory",
                {"Id": dir_id, "Name": os.path.basename(rel_norm)},
            )
            dir_ids[rel_norm] = dir_id
            dir_elements[rel_norm] = dir_el

        target_dir_id = dir_ids[rel_norm]
        for fname in files:
            src_path = os.path.join(root, fname)
            rel_file = fname if rel_norm == "." else f"{rel_norm}/{fname}"
            comp_id = _safe_id("Cmp", rel_file)
            file_id = "SpeedViewExeFile" if rel_file == "SpeedView.exe" else _safe_id("Fil", rel_file)
            comp_guid = str(uuid.uuid5(UUID_NAMESPACE, rel_file)).upper()

            comp_el = ET.SubElement(
                comp_group,
                f"{{{WIX_NS}}}Component",
                {
                    "Id": comp_id,
                    "Directory": target_dir_id,
                    "Guid": comp_guid,
                },
            )
            ET.SubElement(
                comp_el,
                f"{{{WIX_NS}}}File",
                {
                    "Id": file_id,
                    "Source": src_path,
                    "KeyPath": "yes",
                },
            )

    tree = ET.ElementTree(wix_el)
    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate WiX v4 AppFiles.wxs from dist/SpeedView")
    parser.add_argument("--dist-dir", default=os.path.join("dist", "SpeedView"))
    parser.add_argument("--output", default=os.path.join("installer", "windows", "AppFiles.wxs"))
    args = parser.parse_args()
    out = generate_app_files_wxs(args.dist_dir, args.output)
    print(f"Generated WiX component manifest: {out}")


if __name__ == "__main__":
    main()
