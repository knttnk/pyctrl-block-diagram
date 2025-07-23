import control
import numpy as np


def test_show_block_diagram_1():
    import pyctrl_block_diagram as pbd
    P = control.ss(1, 2, 3, 0, name="P", inputs='u', outputs='y')
    print(P)
    K = control.ss(0, 0, 0, -0.5, name="K", inputs='e', outputs='u')
    print(K)
    sumblk = control.summing_junction(inputs=['r', '-y'], output='e')
    T = control.interconnect([P, K, sumblk], inplist='r', outlist='y')
    pbd.show_block_diagram(T)


def test_show_block_diagram_2():
    import pyctrl_block_diagram as pbd
    proc = control.nlsys(
        lambda: None, lambda: None, name="Proc",
        states=2, inputs=['u1', 'u2', 'd'], outputs='y'
    )
    estim = control.nlsys(
        lambda: None, lambda: None, name="Estimator",
        states=2, inputs='y', outputs=['xhat[0]', 'xhat[1]'],
    )
    ctrl = control.nlsys(
        lambda: None, lambda: None, name="Controller",
        states=0, inputs=['r', 'xhat[0]', 'xhat[1]'], outputs=['u1', 'u2'],
    )
    clsys = control.interconnect(
        [proc, estim, ctrl],
        inputs=['r', 'd'], outputs=['y', 'u1', 'u2'],
    )
    pbd.show_block_diagram(clsys)


def test_show_block_diagram_3():
    import pyctrl_block_diagram as pbd
    P = control.ss(
        np.diag([-1, -2, -3, -4]), np.eye(4), np.eye(4), 0, name='P',
        inputs=['u[0]', 'u[1]', 'v[0]', 'v[1]'],
        outputs=['y[0]', 'y[1]', 'z[0]', 'z[1]'])
    C = control.ss(
        [], [], [], [[3, 0], [0, 4]],
        name='C', input_prefix='e', output_prefix='u')
    sumblk = control.summing_junction(
        inputs=['r', '-y'], outputs='e', dimension=2, name='sum')

    clsys1 = control.interconnect(
        [C, P, sumblk],
        connections=[
            ['P.u[0]', 'C.u[0]'], ['P.u[1]', 'C.u[1]'],
            ['C.e[0]', 'sum.e[0]'], ['C.e[1]', 'sum.e[1]'],
            ['sum.y[0]', 'P.y[0]'], ['sum.y[1]', 'P.y[1]'],
        ],
        inplist=['sum.r[0]', 'sum.r[1]', 'P.v[0]', 'P.v[1]'],
        outlist=['P.y[0]', 'P.y[1]', 'P.z[0]', 'P.z[1]', 'C.u[0]', 'C.u[1]']
    )
    clsys2 = control.interconnect(
        [C, P, sumblk],
        connections=[
            ['P.u[0:2]', 'C.u[0:2]'],
            ['C.e[0:2]', 'sum.e[0:2]'],
            ['sum.y[0:2]', 'P.y[0:2]']
        ],
        inplist=['sum.r[0:2]', 'P.v[0:2]'],
        outlist=['P.y[0:2]', 'P.z[0:2]', 'C.u[0:2]']
    )
    clsys3 = control.interconnect(
        [C, P, sumblk],
        connections=[['P.u', 'C.u'], ['C.e', 'sum.e'], ['sum.y', 'P.y']],
        inplist=['sum.r', 'P.v'], outlist=['P.y', 'P.z', 'C.u']
    )
    clsys4 = control.interconnect(
        [C, P, sumblk], name='clsys4',
        connections=[['P.u', 'C'], ['C', 'sum'], ['sum.y', 'P.y']],
        inplist=['sum.r', 'P.v'], outlist=['P', 'C.u']
    )
    clsys5 = control.interconnect(
        [C, P, sumblk], inplist=['sum.r', 'P.v'], outlist=['P', 'C.u']
    )
    htmls = [
        pbd.block_diagram_html(s, for_browser=True)
        for s in [clsys1, clsys2, clsys3, clsys4, clsys5]
    ]
    assert htmls[0] == htmls[1] == htmls[2] == htmls[3] == htmls[4], "Block diagram HTMLs are not equal"
    pbd.show_block_diagram(clsys1)
