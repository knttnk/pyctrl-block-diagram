import control
import webbrowser
import pathlib
import tempfile

# TODO: Make these parameters configurable
# summing_junction_symbol: str = ["Σ", "+", ""][0]
# show_type: bool = True
# show_equations: bool = True
horizontal: bool = False

# path to mermaid.min.js
mermaid_js_path: pathlib.Path = (pathlib.Path(__file__).parent / "mermaid.min.js").absolute()


def block_diagram_html(
    system: control.InterconnectedSystem,
    for_browser: bool = True,
    online: bool = False,
) -> str:
    if for_browser:
        return r"""<!DOCTYPE html>
<html lang="en">
	<head>
""" + ("""<script type="module">
			import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11.9.0/+esm';
		</script>""" if online else f"<script src='{mermaid_js_path}'></script>") + r"""
	</head>
	<body>
		<pre class="mermaid">""" + block_diagram_mermaid_format(system) + r"""</pre>
	</body>
</html>
"""
    else:
        raise NotImplementedError()


def _sanitize(text: str) -> str:
    """
    Sanitize text for use in Mermaid diagrams.
    """
    return text


def _sys_id(sys: control.InputOutputSystem) -> str:
    """
    Define a unique identifier for the system.
    This is used to reference the system in Mermaid diagrams.
    """
    not_allowed_chars = r" .-[]{}()<>\/"
    name = sys.name
    for char in not_allowed_chars:
        name = name.replace(char, "")
    return name


def block_diagram_mermaid_format(system: control.InterconnectedSystem) -> str:
    """
    Convert the system to a Mermaid format string.
    """
    # def signal_sys_name(index: int) -> str:
    #     """
    #     Return the name of the system for use in Mermaid diagrams.
    #     """
    #     if show_type:
    #         return f"{sys.name} [{sys.__class__.__name__}]"
    #     return sys.name

    config_part = r"""
---
displayMode: compact
config:
    theme: base
    themeVariables:
        darkMode: false
        fontFamily:  verdana
        background: '#fff'
        primaryColor: '#fff'
        primaryTextColor: '#000'
        primaryBorderColor: '#000'
        secondaryColor: '#fff'
        secondaryTextColor: '#000'
        secondaryBorderColor: '#000'
        lineColor: '#888'
        textColor: '#000'
---
"""

    # Define a utility function to generate the signal

    def cxn_string(signal: str, gain: float, first: bool) -> str:
        """
        Example:
            cxn_string("K.y", 1, True) -> "K.y"
            cxn_string("e", -1, False) -> " - e"
            cxn_string("u", 2, True) -> " + 2 * u"
            cxn_string("u", -3, False) -> " - 3 * u"
        """
        if gain == 1:
            return (" + " if not first else "") + f"{signal}"
        elif gain == -1:
            return (" - " if not first else "-") + f"{signal}"
        elif gain > 0:
            return (" + " if not first else "") + f"{gain} {signal}"
        elif gain < 0:
            return (" - " if not first else "-") + \
                f"{abs(gain)} {signal}"
        else:
            raise ValueError(f"Invalid gain value: {gain}")

    connection_parts = []
    # add input connections
    input_dstsigs, input_srcsigs, input_dsts = [], [], []
    for subsys in system.syslist:
        input_dstsigs += [subsys.name + "." + lbl for lbl in subsys.input_labels]  # like ['K.e', ...]
        input_srcsigs += [lbl for lbl in system.input_labels]  # like ['e', ...]
        input_dsts += [subsys for _ in subsys.input_labels]  # like [Sys('K'), ...]
    for i_r, row in enumerate(system.input_map):
        for i_c, gain in enumerate(row):
            if not gain:
                continue
            srcsig, dstsig, dstsys = (
                input_srcsigs[i_c],
                input_dstsigs[i_r],
                input_dsts[i_r],
            )
            srcsig = cxn_string(srcsig, gain, first=True)
            connection_parts.append(
                f'input -- "{_sanitize(dstsig)} ← {_sanitize(srcsig)}" --> {_sys_id(dstsys)}'
            )
    # add output connections
    output_dstsigs, output_srcsigs, output_srcs = [], [], []
    for subsys in system.syslist:
        output_srcsigs += [subsys.name + "." + lbl for lbl in subsys.output_labels]  # like ['y', ...]
        output_dstsigs += [lbl for lbl in system.output_labels]  # like ['P.y', ...]
        output_srcs += [subsys for _ in subsys.output_labels]  # like [Sys('P'), ...]
    for i_r, row in enumerate(system.output_map):
        for i_c, gain in enumerate(row):  # type: ignore
            if not gain:
                continue
            srcsig, dstsig, srcsys = (
                output_srcsigs[i_c],
                output_dstsigs[i_r],
                output_srcs[i_r],
            )
            srcsig = cxn_string(srcsig, gain, first=True)
            connection_parts.append(
                f'{_sys_id(srcsys)} -- "{_sanitize(dstsig)} ← {_sanitize(srcsig)}" --> output'
            )
    # add internal connections
    internal_dstsigs, internal_srcsigs, internal_dsts, internal_srcs = [], [], [], []
    for subsys in system.syslist:
        internal_dstsigs += [subsys.name + "." + lbl for lbl in subsys.input_labels]  # like ['P.u', ...]
        internal_srcsigs += [subsys.name + "." + lbl for lbl in subsys.output_labels]  # like ['K.u', ...]
        internal_dsts += [subsys for _ in subsys.input_labels]  # like [Sys('P'), ...]
        internal_srcs += [subsys for _ in subsys.output_labels]  # like [Sys('K'), ...]
    for i_r, row in enumerate(system.connect_map):
        for i_c, gain in enumerate(row):
            if not gain:
                continue
            srcsig, srcsys, dstsig, dstsys = (
                internal_srcsigs[i_c],
                internal_srcs[i_c],
                internal_dstsigs[i_r],
                internal_dsts[i_r],
            )
            srcsig = cxn_string(srcsig, gain, first=True)
            # first = (i_c == 0)
            connection_parts.append(
                f'    {_sys_id(srcsys)} -- "{_sanitize(dstsig)} ← {_sanitize(srcsig)}" --> {_sys_id(dstsys)}'
            )

    # sumJun1@{ shape: sm-circ }
    # K["$$K$$"]
    # P["$$P\ :\begin{cases}\begin{aligned} \dot{x}(t) & = Ax(t) + Bu(t) \\\\ y(t) & = Cx(t) + Du(t) \end{aligned}\end{cases}$$"]
    # sep1@{ shape: f-circ }
    # input -->|"$$r$$"| sumJun1
    # +9 --> |"$$e$$"| K
    # P --> |"$$y$$"| sep1
    # sep1 --> |"$$y$$"| output
    # K --> |"$$u$$"| P
    # sep1 --> |"$$-1 \times y$$"| sumJun1
    main_part = r"""
flowchart """ + ("LR" if horizontal else "TD") + r"""
    input@{ shape: stadium }
    output@{ shape: stadium }
""" + "\n".join(
        [  # System nodes
            f'    {_sys_id(s)}["{_sanitize(s.name)}"]'
            for s in system.syslist
        ] + connection_parts
    ) + r"""
classDef inout fill:#7ca;
class input,output inout
"""
    return config_part + main_part


def show_block_diagram(system: control.InterconnectedSystem) -> None:
    """
    Show the block diagram of the system in a web browser.
    """
    html = block_diagram_html(system)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
        f.write(html.encode())
        print(f"Block diagram saved to {f.name}")
        webbrowser.open(f.name)
