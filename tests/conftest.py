import io

import pytest

from core.parser import load_jtl

# 4 samples, 2 labels, 1 failure. Timestamps are one second apart.
SAMPLE_CSV = """timeStamp,elapsed,label,responseCode,responseMessage,threadName,success,failureMessage,bytes,sentBytes,grpThreads,allThreads,Latency,Connect
1700000000000,100,A,200,OK,TG 1-1,true,,1024,100,1,2,80,10
1700000001000,300,A,200,OK,TG 1-2,true,,2048,100,2,4,200,20
1700000002000,2000,B,500,Server Error,TG 1-1,false,Assertion failed,512,100,1,2,1500,30
1700000003000,700,B,200,OK,TG 1-2,true,,512,100,1,2,500,30
"""


@pytest.fixture
def jtl():
    return load_jtl(io.StringIO(SAMPLE_CSV))


@pytest.fixture
def frame(jtl):
    return jtl.df
