"""

stochastic.py: This module calculates hazard rates (also called
failure rates) as used in system reliability modeling.

A hazard rate is based upon conditional probabilities.  It is 
the failure probability per unit of time at time t, given that
a failure has not yet occurred at time t.

A conditional probability is defined as: 
        P(A|B) = P(intersection(A,B)) / P(B).

Similarly, a hazard function is defined as:
        h(t) = f(t) / R(t), 
where f(t) is a probability density function (pdf) and R(t) is the 
reliability function.

If f(t) models the instantaneous probability of a component failing
at time t, then R(t) is the probability that the component is still
functioning at time t.  F(t) is the probability that a component
has failed at time t.  This is the area under the pdf curve up to 
time t.  The reliability function is defined as: R(t) = 1 - F(t).
This is the area under the pdf curve beyond time t.

References:
1) Trivedi, Kishor S. "Probability and Statistics with Reliability,
Queuing and Computer Science Applications", 2nd ed.

2) Shooman, Martin L. "Reliability of Computer Systems and Networks:
Fault Tolerance, Analysis, and Design", 1st ed.

3) Grosh, Doris L. "A Primer of Reliability Theory", 1st ed.

4) Hayter, Anthony. "Probability and Statistics For Engineers and
Scientists", 4th ed.

The hazard functions in this module determine whether an event has
occurred at a moment in time based upon a model.  A probability
is calculated according to a hazard rate.  Whether the event occurs
depends upon a random value retrieved from Python's pseudo-random number
generator.  This is a uniformly distributed random number generated
by the Mersenne Twister algorithm in the semi-open range [0.0, 1.0). 
"""

from collections import namedtuple
import math
import random


def exponential_hazard(mttf):
    """ A exponentially distributed hazard rate function.
        This is a Poisson distribution, which describes the probability
        of a number of events occurring in a fixed interval of time.
        The probability of an event occurring is independent of the
        occurrence of the previous event.
        This hazard function is also called the constant failure rate
        (CFR). It also happens to be a special case of the Weibull
        hazard function - when the shape parameter is 1.

        This function is useful in Havoc when events should arrive in
        very unpredictable intervals.

        mttf: mean time to failure (in seconds) in reliability engineering
        returns: true or false; true if the hazard has occurred at
            function call time.
    """
    lambda_ = 1.0 / mttf
    return random.random() <= lambda_


def normal_hazard(mu, sigma, t):
    """ A normal or Guassian distributed hazard rate function.
        This is an increasing failure rate (IFR).  This indicates
        that the probability of an event increases monotonically
        as time progresses.

        This function is useful in Havoc events should arrive in
        very predictable intervals.  Decreasing the standard deviation
        will increase this predictability.

        mu: this will be the mean time to failure (in seconds)
            in reliability engineering
        sigma: standard deviation in seconds
        t: elapsed time in seconds since the last event
        returns: true or false; true if the hazard has occurred at
            the elapsed time.
    """
    p1 = _normal_distributed(mu,sigma,t)
    z = _z_table_search((t-mu)/float(sigma))
    if z is None:
        return False
    p2 = p1/(1-z)
    return random.random() <= p2


def weibull_hazard(a, mttf, t):
    """ A Weibull distributed hazard rate function.  This hazard rate
        is frequently used in reliability engineering because it allows
        all phases of a compenents life to be modeled.  The phases are
        controlled by the shape parameter ('a').  A shape parameter less
        than one is a decreasing failure rate (DFR).  This indicates
        that the probability of an event decreases monotonically as time
        progresses.  A DFR is used to model the break-in or debugging
        phases of a component.  It allows for the possibility that the
        event never occurs.  A shape parameter equal to 1 reduces to
        the special case of an exponentially distributed hazard rate.  A
        shape parameter greater than one is an increasing failure rate (IFR).
        This indicates that the probability of an event increases
        monotonically as time progresses.  The IFR is used to model the 
        wear-out phase of a component or can be used to model a component
        which leaks resources such as memory.  

        Weibull hazard functions are paramaterized in varying ways in
        different sources.  This implementation uses a simple version as
        found in the "Reliability Analysis and Life Testing" chapter of
        Ref. 4. 

        a: determines the shape (ie. 1 = constant failure rate (CFR),
                                   > 1 = increasing failure rate (IFR),
                                      (a larger value provides a steeper
                                       increase in hazard probability)
                                     2 = linearly increasing failure rate,
                                   < 1 = decreasing failure rate (DFR)).
        mttf: mean time to failure (in seconds) reliability engineering 
            (Note: mttf is a slight abuse of statistical precision for 
            the Weibull hazard function, ease of use is more desirable 
            for this application)
        returns: true or false; true if the hazard has occurred at
            the elapsed time.
    """
    lambda_ = 1.0 / mttf
    p = a*math.pow(lambda_,a) * math.pow(t,a-1)
    return random.random() <= p


def _normal_distributed(mu, sigma, t):
    """ A normal or Gaussian distribution probability
        density function.

        mu: this will be the mean time to failure (in seconds)
            in reliability engineering
        sigma: standard deviation in seconds
        t: elapsed time in seconds since the previous event
        returns: an instantaneous probability
    """
    f1 = 1.0/(sigma*math.sqrt(2*math.pi))
    f2 = math.exp(-0.5*math.pow((t-mu)/float(sigma),2))
    return f1*f2


def _z_table_search(z_in):
    """ A binary search of Z_TABLE.  Matching is based
        on finding the best range fit for z_in.

        z_in: the z-value
        returns: the cumulative probability
    """
    l,u = 0,_Z_TABLE_LEN-2
    while l <= u:
        m = (l+u) // 2  
        if _Z_TABLE[m].z <= z_in and _Z_TABLE[m+1].z > z_in:
            return _Z_TABLE[m].area
        elif _Z_TABLE[m].z > z_in:
            u = m-1
        else:
            l = m+1


# A Standard Normal (Z) table.
# It consists of the standard normal critical points as provided in
# Table T1 of Ref. 3.
_cell = namedtuple('_cell', ['area','z'])
_Z_TABLE_LEN = 107
_Z_TABLE = [_cell(.0001,-3.719),_cell(.005,-2.576),_cell(.001,-3.09),
            _cell(.01,-2.326),_cell(.02,-2.054),_cell(.025,-1.96),
            _cell(.03,-1.881),_cell(.04,-1.751),_cell(.05,-1.645),
            _cell(.06,-1.555),_cell(.07,-1.476),_cell(.08,-1.405),
            _cell(.09,-1.341),_cell(.10,-1.282),_cell(.11,-1.227),
            _cell(.12,-1.175),_cell(.13,-1.126),_cell(.14,-1.080),
            _cell(.15,-1.036),_cell(.16,-0.994),_cell(.17,-0.954),
            _cell(.18,-0.915),_cell(.19,-0.878),_cell(.20,-0.842),
            _cell(.21,-0.806),_cell(.22,-0.772),_cell(.23,-0.739),
            _cell(.24,-0.706),_cell(.25,-0.674),_cell(.26,-0.643),
            _cell(.27,-0.613),_cell(.28,-0.583),_cell(.29,-0.553),
            _cell(.30,-0.524),_cell(.31,-0.496),_cell(.32,-0.468),
            _cell(.33,-0.440),_cell(.34,-0.412),_cell(.35,-0.385),
            _cell(.36,-0.358),_cell(.37,-0.332),_cell(.38,-0.305),
            _cell(.39,-0.279),_cell(.40,-0.253),_cell(.41,-0.228),
            _cell(.42,-0.202),_cell(.43,-0.176),_cell(.44,-0.151),
            _cell(.45,-0.126),_cell(.46,-0.100),_cell(.47,-0.075),
            _cell(.48,-0.050),_cell(.49,-0.025),_cell(.50,0.000),
            _cell(.51,0.025),_cell(.52,0.050),_cell(.53,0.075),
            _cell(.54,0.100),_cell(.55,0.126),_cell(.56,0.151),
            _cell(.57,0.176),_cell(.58,0.202),_cell(.59,0.228),
            _cell(.60,0.253),_cell(.61,0.279),_cell(.62,0.305),
            _cell(.63,0.332),_cell(.64,0.358),_cell(.65,0.385),
            _cell(.66,0.412),_cell(.67,0.440),_cell(.68,0.468),
            _cell(.69,0.496),_cell(.70,0.524),_cell(.71,0.553),
            _cell(.72,0.583),_cell(.73,0.613),_cell(.74,0.643),
            _cell(.75,0.674),_cell(.76,0.706),_cell(.77,0.739),
            _cell(.78,0.772),_cell(.79,0.806),_cell(.80,0.842),
            _cell(.81,0.878),_cell(.82,0.915),_cell(.83,0.954),
            _cell(.84,0.994),_cell(.85,1.036),_cell(.86,1.080),
            _cell(.87,1.126),_cell(.88,1.175),_cell(.89,1.227),
            _cell(.90,1.282),_cell(.91,1.341),_cell(.92,1.405),
            _cell(.93,1.476),_cell(.94,1.555),_cell(.95,1.645),
            _cell(.96,1.751),_cell(.97,1.881),_cell(.975,1.960),
            _cell(.98,2.054),_cell(.99,2.326),_cell(.999,3.090),
            _cell(.9995,3.290),_cell(.9999,3.719)]
