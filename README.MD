# SpecMerger

This tool was developped in the Systems and Formalism Lab at EPFL.

For a full understanding of the project, please read this [blogspot](https://systemf.epfl.ch/blog/SpecMerger) that explains it in great details.

This tool can be used to compare two trees that were constructed with special Nodes provided in the project.

This can be very useful to compare two structured documents that should have the same content, like for example
a specification and its implementation (by having the specification text in comments on top of actual lines of code) or 
if you just have two different data formats that need to have the same content.

To use this tool, you will first need to write a Parser to generate a `ParsedPage` for each document.
After this you can use the following code to see a nice comparison in the form of an HTML document.

```python
from spec_merger.aligner import Aligner
from spec_merger.html_renderer import HTMLRenderer
import webbrowser, os
# p1 is ParsedPage n°1, p2 is n°2
aligner = Aligner()
result = aligner.align(p1,p2)
rendered = HTMLRenderer(result).render(path_to_template="spec_merger")
with open("comparison.html", "w+") as f:
    f.write(rendered)
webbrowser.open(f"file://{os.path.abspath('comparison.html')}", 2)
```

## Type of nodes in the tree
The diferent existing nodes can all be found in the content_classes folder, which are :
- String
- Dictionary
- OrderedDictionary
- Bag (a set)
- OrderedSeq (a list)
- WildCard (matches anything)

If you need to create another type of node, just create a new class in the folder by inspiring yourself of the other ones.

Whenever you instantiate the aligner, you can pass it a dictionary that takes a pair of types and returns a function of type `Content,Content -> Content`.
This function will then be called whenever the tool needs to compare two nodes that have the correct types.

Here is an example:
```python
from spec_merger.content_classes.dictionary import Dictionary
from spec_merger.content_classes.string import String
from spec_merger.content_classes.misalignment import Misalignment
from spec_merger.aligner_utils import ReportErrorType
from spec_merger.aligner import Aligner

fn_map = {(Dictionary, String): lambda dic,str: Misalignment((dic.position,str.position),dic,str,ReportErrorType.MISMATCHED_TYPES)}
aligner = Aligner(fn_map)
# Now aligner will call this specific function whenever it is comparing a Dictionary and a String
```

If you wish to have a type that has very special behaviour, like the WildCard, you can modify the `special comparator` function, to do whatever behaviour you want.
Note however that this function will only be called if the pair of types was not found in the function_map.

## Example
You can have a look at the test-example folder, it contains a very minimal example for a JSONParser.
If you want to have a look at a bigger project where it was used, have a look at [Warblre](https://github.com/epfl-systemf/Warblre).