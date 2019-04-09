
class ISRweight:

  def __init__(self):
    #Parameters for 2016 data
    self.weights    = [1, 0.920, 0.821, 0.715, 0.662, 0.561, 0.511]
    self.norm       = 1.071
    self.njet_max   = len(self.weights)-1

  def getWeightString(self):

    self.weightStr = '( '

    for njet, weight in enumerate(self.weights):
      op = '=='
      if njet == self.njet_max: op = '>='
      self.weightStr += '{}*(nIsr{}{}) + '.format(weight,op,njet)

    self.weightStr += ' 0 )'

    return self.weightStr
    
  def getWeight(self, r):
    return self.norm*self.weights[r.nIsr] if r.nIsr <= self.njet_max else self.norm*self.weights[self.njet_max]
