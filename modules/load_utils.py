import tempfile


def save_uploaded_file(uploaded_file):

    suffix = "." + uploaded_file.name.split(".")[-1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as tmp:

        tmp.write(uploaded_file.getbuffer())

        return tmp.name