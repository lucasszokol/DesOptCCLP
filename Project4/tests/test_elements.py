import numpy as np

from heatsink.elements import line_conduction_matrix, quad4_conduction_matrix


def test_line_element_is_symmetric_and_conservative() -> None:
    matrix = line_conduction_matrix(167.0, 5.0e-5, 0.04)
    np.testing.assert_allclose(matrix, matrix.T)
    np.testing.assert_allclose(matrix @ np.ones(2), 0.0, atol=1.0e-12)


def test_quad_element_is_symmetric_and_conservative() -> None:
    coordinates = np.array([[0.0, 0.0], [2.0, 0.0], [2.0, 1.0], [0.0, 1.0]])
    matrix = quad4_conduction_matrix(coordinates, conductivity=3.0, depth=0.5)
    np.testing.assert_allclose(matrix, matrix.T, atol=1.0e-13)
    np.testing.assert_allclose(matrix @ np.ones(4), 0.0, atol=1.0e-12)
    eigenvalues = np.linalg.eigvalsh(matrix)
    assert eigenvalues[0] > -1.0e-12
    assert eigenvalues[1] > 0.0
