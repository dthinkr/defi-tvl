import streamlit as st
from streamlit_observable import observable

observers = observable("Example form", 
    notebook="@mbostock/form-input",
    targets=["viewof object"],
    observe=["object"]
)

o = observers.get("object")

if o is not None:
    st.write("message: **'{message}'**, hue: '{hue}', size: '{size}', emojis: '{emojis}'".format(
        message=o.get("message"),
        hue=o.get("hue"),
        size=o.get("size"),
        emojis=str(o.get("emojis"))
    ))