from src.steelopt import *
S=Stock('S','A',6000,2000,'S355',12)
P=[Part('1','A',2000,900,'S355',12),Part('2','A',1500,700,'S355',12)]

def test_packing_valid():
    placed,unplaced=pack_shelves(S,P)
    assert not unplaced and not validate_layout(S,P,placed)

def test_overlap_rejected():
    a=Placement('S','1',0,0,2000,900,False)
    b=Placement('S','2',1000,0,1500,700,False)
    assert any('collision' in x for x in validate_layout(S,P,[a,b]))

def test_kerf_rejected():
    a=Placement('S','1',0,0,2000,900,False)
    b=Placement('S','2',2002,0,1500,700,False)
    assert any('kerf' in x for x in validate_layout(S,P,[a,b],5))

def test_bounds_rejected():
    a=Placement('S','1',5000,0,2000,900,False)
    assert any('bounds' in x for x in validate_layout(S,P,[a]))

def test_incompatible_material():
    assert not compatible(S,Part('x','A',500,500,'S275',12))
    assert not compatible(S,Part('x','A',500,500,'S355',10))

def test_offcut_gate():
    good=Stock('O1','A',1800,900,'S355',12,'offcut',unit_cost_per_m2=6400)
    wrong=Stock('O2','A',1800,900,'S355',10,'offcut')
    quarantined=Stock('O3','A',1800,900,'S355',12,'offcut','quarantined')
    notrace=Stock('O4','A',1800,900,'S355',12,'offcut','available',False)
    matched=offcut_matches([Part('B1','B',1500,700,'S355',12)],[good,wrong,quarantined,notrace])
    assert [m['offcut_id'] for m in matched]==['O1']
    assert matched[0]['decision']=='PENDING_COST_CONTROL_APPROVAL'
    assert matched[0]['realized_savings'] is None

def test_no_false_fit_and_rotation_gate():
    o=Stock('O','A',1800,900,'S355',12,'offcut')
    assert not offcut_matches([Part('x','A',1800,900,'S355',12)],[o],kerf=5)
    assert not offcut_matches([Part('x','A',700,1500,'S355',12,False)],[o])

def test_invalid_input_kerf():
    import pytest
    with pytest.raises(ValueError): pack_shelves(S,P,-1)
