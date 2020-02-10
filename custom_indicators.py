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


class RelativeVigorIndex(bt.Indicator):
    lines = ('RVI', 'Signal',)
    params = dict(period=20, movav=bt.ind.MovAv.Simple)

    def __init__(self):
        self.addminperiod(self.p.period)
        self.a = self.data.close(0) - self.data.open(0)
        self.b = self.data.close(-1) - self.data.open(-1)
        self.c = self.data.close(-2) - self.data.open(-2)
        self.d = self.data.close(-3) - self.data.open(-3)
        self.e = self.data.high(0) - self.data.low(0)
        self.f = self.data.high(-1) - self.data.low(-1)
        self.g = self.data.high(-2) - self.data.low(-2)
        self.h = self.data.high(-3) - self.data.low(-3)
        self.numerator = (self.a + (2 * self.b) + (2 * self.c) + self.d) / 6
        self.denominator = (self.e + (2 * self.f) + (2 * self.g) + self.h) / 6
        # self.lines.Signal = bt.Max(0.0, self.params.days_prior)
        self.sma_num = self.p.movav(self.numerator, period=self.p.period)
        self.sma_den = self.p.movav(self.denominator, period=self.p.period)
        self.lines.RVI = self.sma_num / self.sma_den
        self.i = self.lines.RVI(-1)
        self.j = self.lines.RVI(-2)
        self.k = self.lines.RVI(-3)
        self.lines.Signal = (self.lines.RVI + (2 * self.i) + (2 * self.j) + self.k) / 6
