# Blender Scripts

## WRL to OBJ
If your level geometry is not sealed or is otherwise non-manifold, tool.exe will produce a corresponding `.wrl` file in your working directory which contains some "debug geometry". It's helpful to import this into your 3D software to see where the errors are and correct them.

Unfortunately, its VRML 1.0 file format is unsupported by Blender (its VRML plugin only supports 2.0). This script performs a basic conversion of the file to an OBJ file containing edge segments, which can be imported by Blender.

### Usage
This script relies on the Python package `tatsu`. Firstly, ensure that is installed with `pip install --user tatsu`. The script can then be invoked on the command line like so:

```sh
# given file paths for input and output:
python wrl-to-obj.py --input input.wrl --output output.obj

# from stdin to stdout:
python wrl-to-obj.py < input.wrl > output.obj
```

When importing the `.obj` into Blender, be sure to use **Y forward and Z up** settings. I recommend setting the imported object's viewport display to "In Front" and selecting the object so it's easier to see. If your map has a number of materials it can also help to switch to single colour viewport shading.

![](resources/wrl-errors.png)
