from typing import Sequence, Any
from .exceptions import MismatchedSequenceLengthError

def validate_common_size(**seqs: Sequence[Any]):
    seq_lens = [len(seq) for _, seq in seqs.items()]
    if not seq_lens:
        return
    initial_seq_len = seq_lens[0]
    if not all([initial_seq_len == seq_len for seq_len in seq_lens]):
        raise MismatchedSequenceLengthError(**seqs)
