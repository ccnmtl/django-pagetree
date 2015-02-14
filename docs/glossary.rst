Glossary
============

This is a glossary of terms used in pagetree.

.. glossary::

section
    A "section" in pagetree refers to a node in the tree. A section can
    be thought of as a page in your hierarchy. Keep in mind that each
    section can contain any number of child sections.

locked / unlocked
    If a section is "locked", that means the user can't navigate past it
    with the "next" button.

gating / is_gated
    Gating is a feature that prevents users from visiting a section if
    they haven't visited all the preceding sections. If a pagetree site
    is "gated" and you try to visit a section in the middle of the tree
    with a new user, you will be redirected to the first node (or
    "section") in the tree.
