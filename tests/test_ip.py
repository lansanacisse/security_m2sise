from views.analysis import is_internal_ip


def test_internal_ips():
    """Test des adresses IP internes valides"""
    assert is_internal_ip("10.0.0.1") == True
    assert is_internal_ip("172.16.0.1") == True
    assert is_internal_ip("172.31.255.255") == True
    assert is_internal_ip("192.168.1.1") == True


def test_boundary_cases():
    """Test des cas limites"""
    assert is_internal_ip("10.0.0.0") == True  # Début de plage
    assert is_internal_ip("10.255.255.255") == True  # Fin de plage
    assert is_internal_ip("172.16.0.0") == True  # Début de plage
    assert is_internal_ip("172.31.255.255") == True  # Fin de plage
    assert is_internal_ip("192.168.0.0") == True  # Début de plage
    assert is_internal_ip("192.168.255.255") == True  # Fin de plage


def test_invalid_ips():
    """Test des adresses IP invalides"""
    assert is_internal_ip("256.256.256.256") == False
    assert is_internal_ip("not_an_ip") == False
    assert is_internal_ip("192.168.1") == False
    assert is_internal_ip("") == False


def test_edge_cases():
    """Test des cas particuliers"""
    assert is_internal_ip("0.0.0.0") == False  # Adresse non routée
    assert is_internal_ip("127.0.0.1") == False  # Localhost
    assert is_internal_ip("255.255.255.255") == False  # Broadcast
