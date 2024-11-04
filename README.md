# conn-sqla-file-extender

SqlAlchemy File type code extender explicitly designed for connexion servers, for easy file management.

## Main functionality

### Detects File Type objects

The plugin heuristically loads your python file in the target directory, detect any class that has inherited the declarative_base class, and identifies every field that is of file type (Binary, Blob)

### Generates file getter and setter objects

Based on you connexion settings, it generates either a werkzeug, or scarlette file handler, that will help you load your file with a single setter and getter.

### Propose additional fields.

To enable saving metadata, it looks up or proposes generic fields, like mime_type or file_name
