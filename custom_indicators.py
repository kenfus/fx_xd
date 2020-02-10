import backtrader as bt
import numpy as np

class schaff_trend_cycle(bt.ind.PeriodN):
    lines = ('schaff_cycle', 'f1', 'f2', 'pf',)

    params = (('length', 20),
              ('slowLength', 23),
              ('fastLength', 50),
              ('factor', 0.5),
              )

    def __init__(self):
        self.m = bt.ind.MACDHisto(self.data.close, period_me1=self.p.fastLength, period_me2=self.p.slowLength)
        self.v1 = bt.ind.Lowest(self.m, period=self.p.length)
        self.v2 = bt.ind.Highest(self.m, period=self.p.length) - self.v1
        self.l.f1 = bt.If(self.v2 > 0, (self.m - self.v1) / self.v2 * 100, self.lines.f1(-1))
        self.l.pf = self.l.pf(-1) + (self.p.factor * (self.l.f1 - self.l.pf(-1)))
        self.v3 = bt.ind.Lowest(self.l.pf, period=self.p.length)
        self.v4 = bt.ind.Highest(self.l.pf, period=self.p.length) - self.v3
        self.l.f2 = bt.If(self.v4 > 0, ((self.l.pf - self.v3) / self.v4) * 100, self.l.f2(-1))
        self.l.schaff_cycle = self.l.schaff_cycle(-1) + (
                self.p.factor * (self.l.f2 - self.l.schaff_cycle(-1)))

    def nextstart(self):
        self.l.f2[0] = 0.0
        self.l.pf[0] = 0.0
        self.l.schaff_cycle[0] = 0.0