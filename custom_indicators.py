import backtrader as bt
import numpy as np

class SchaffTrendCycle(bt.ind.PeriodN):
    lines = ('schaff_cycle',)
    alias = ('STC')
    params = (('length', 20),
              ('slowLength', 23),
              ('fastLength', 50),
              ('factor', 0.5),
              )

    def __init__(self):
        self.m = bt.ind.MACDHisto(self.data.close, period_me1=self.p.fastLength, period_me2=self.p.slowLength)
        self.v1 = bt.ind.Lowest(self.m, period=self.p.length)
        self.v2 = bt.ind.Highest(self.m, period=self.p.length) - self.v1

    def next(self):
        self.f1[0] = (self.m[0] - self.v1[0]) / self.v2[0] * 100 if self.v2[0] > 0 else self.f1[-1]
        self.pf[0] = self.pf[-1] + (self.p.factor * (self.f1[0] - self.pf[-1]))
        self.v3 = bt.ind.Lowest(self.pf, period=self.p.length)
        self.v4 = bt.ind.Highest(self.pf, period=self.p.length) - self.v3
        self.f2[0] = ((self.pf[0] - self.v3[0]) / self.v4[0]) * 100 if self.v4[0] > 0 else self.f2[-1]
        self.l.schaff_cycle[0] = self.l.schaff_cycle[-1] + (
                self.p.factor * (self.f2[0] - self.l.schaff_cycle[-1]))

    def nextstart(self):  # calculate here the seed value
        self.f1[0] = sum(self.data.get(size=self.p.length)) / self.p.length
        self.pf[0] = sum(self.data.get(size=self.p.length)) / self.p.length
        self.f2[0] = sum(self.data.get(size=self.p.length)) / self.p.length


class RelativeVigorIndex(bt.Indicator):
    lines = ('RVI',)
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

class RelativeVigorIndexSignal(bt.Indicator):
    lines = ('Signal',)
    params = dict(period=20, movav=bt.ind.MovAv.Simple)

    def __init__(self):
        self.addminperiod(self.p.period)
        self.lines.RVI = RelativeVigorIndex()
        self.i = self.lines.RVI(-1)
        self.j = self.lines.RVI(-2)
        self.k = self.lines.RVI(-3)
        self.lines.Signal = (self.lines.RVI + (2 * self.i) + (2 * self.j) + self.k) / 6

 class RelativeVigorIndexWithSignal(bt.Indicator):
    lines = ('RVI', 'Signal',)
    params = dict(period=20, movav=bt.ind.MovAv.Simple)

    def __init__(self):
        self.addminperiod(self.p.period)
        self.lines.RVI = RelativeVigorIndex()
        self.lines.Signal = RelativeVigorIndexSignal()

class SelfAdjustingRelativeStrengthIndex(bt.Indicator):
    lines = ('srsi', 'upper', 'lower',)
    params = dict(period=20, movav=bt.ind.MovAv.Simple)

    def __init__(self):
        self.addminperiod(self.p.period)
        self.lines.srsi = bt.ind.RelativeStrengthIndex()
        self.lines.upper = 50 + 1.8 * bt.ind.StandardDeviation(self.srsi, period=self.p.period)
        self.lines.lower = 50 - 1.8 * bt.ind.StandardDeviation(self.srsi, period=self.p.period)

class VolatilityQualityZeroLine(bt.Indicator):
    lines = ('vqzl',)
    params = dict(PriceSmoothing=7, movav=bt.ind.WeightedMovingAverage)

    def __init__(self):
        self.cHigh = self.p.movav(self.data.high, period=self.p.PriceSmoothing)
        self.cLow = self.p.movav(self.data.low, period=self.p.PriceSmoothing)
        self.cOpen = self.p.movav(self.data.open, period=self.p.PriceSmoothing)
        self.cClose = self.p.movav(self.data.close, period=self.p.PriceSmoothing)
        self.trueRange = bt.ind.Highest(self.cHigh, self.cClose) - bt.ind.Lowest(self.cLow, self.cClose(-1))
        self.rrange = self.cHigh - self.cLow
        try:
            self.l.vqi = (self.cClose - self.cClose(-1)) / self.trueRange + (
                        self.cClose - self.cOpen) / self.rrange * 0.5
        except:
            self.l.vqi = self.l.vqi(-1)
        self.l.vqzl = abs(self.l.vqi) * (self.cClose - self.cClose(-1) + self.cClose - self.cOpen) * 1000
