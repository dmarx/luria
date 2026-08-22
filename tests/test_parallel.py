import os
import pytest
from luria import parallel

def test_results_keep_input_order():
    assert parallel.pmap(lambda x: x * 2, range(50)) == [x * 2 for x in range(50)]

def test_exceptions_propagate_like_map():

    def boom(x):
        if x == 3:
            raise ValueError('x was 3')
        return x
    with pytest.raises(ValueError, match='x was 3'):
        parallel.pmap(boom, range(10))

def test_jobs_env_forces_serial(monkeypatch):
    monkeypatch.setenv('LURIA_JOBS', '1')
    assert parallel.jobs() == 1
    assert parallel.pmap(lambda x: x + 1, [1, 2, 3]) == [2, 3, 4]

def test_jobs_env_garbage_falls_back_to_default(monkeypatch):
    monkeypatch.setenv('LURIA_JOBS', 'many')
    assert parallel.jobs() == parallel.DEFAULT_JOBS

def test_empty_input_is_fine():
    assert parallel.pmap(lambda x: x, []) == []

def test_outputs_identical_at_any_width(monkeypatch):
    from luria import adr_index
    monkeypatch.setenv('LURIA_JOBS', '1')
    serial = adr_index.outputs()
    monkeypatch.delenv('LURIA_JOBS')
    assert adr_index.outputs() == serial
