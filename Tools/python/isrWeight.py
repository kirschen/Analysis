
class ISRweight:

  def __init__(self):
    #Parameters for 2016 data
    self.weights    = [1, 0.920, 0.821, 0.715, 0.662, 0.561, 0.511]
    self.weights_syst = [0.0, 0.040, 0.090, 0.143, 0.169, 0.219, 0.244]
    self.norm       = 1.071
    self.njet_max   = len(self.weights)-1

  def getWeightString(self, sigma=0):

    weights = [ w+(sigma*self.weights_syst[i]) for i, w in enumerate(self.weights)]
    weightStr = '( '

    for njet, weight in enumerate(weights):
      op = '=='
      if njet == self.njet_max: op = '>='
      weightStr += '{}*(nISR{}{}) + '.format(weight,op,njet)

    weightStr += ' 0 )'

    return weightStr
    
  def getWeight(self, r, sigma=0):
    weights = [ w+(sigma*self.weights_syst[i]) for i, w in enumerate(self.weights)]
    return self.norm*weights[r.nISR] if r.nISR <= self.njet_max else self.norm*weights[self.njet_max]
