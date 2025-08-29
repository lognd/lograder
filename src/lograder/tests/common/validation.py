from typing import Any, Sequence

from .exceptions import MismatchedSequenceLengthError, NonSingleArgumentSpecifiedError


def validate_common_size(**seqs: Sequence[Any]):
    seq_lens = [len(seq) for _, seq in seqs.items()]
    if not seq_lens:
        return
    initial_seq_len = seq_lens[0]
    if not all([initial_seq_len == seq_len for seq_len in seq_lens]):
        raise MismatchedSequenceLengthError(**seqs)


def validate_unique_argument(**kwargs: Any):
    if sum([val is None for val in kwargs.values()]) != 1:
        raise NonSingleArgumentSpecifiedError(**kwargs)
