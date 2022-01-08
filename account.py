class Account:
    '''
    an imaginary investing account

    Instance variables:
    capital: float
    equity: dict
    '''

    def __init__(self, starting_capital: float, equity={}):
        '''
        initialize the account with a starting capital and holding stocks
        '''
        self.__starting_capital = starting_capital
        self.__max_win = 0
        self.__max_loss = 0
        self.__last_investment = self.__starting_capital
        self.capital = starting_capital
        self.equity = equity

    def get_current_capital(self) -> float:
        return self.capital

    def get_starting_capital(self) -> float:
        return self.__starting_capital

    def withdraw_captial(self, amount: float) -> float:
        if self.capital >= amount:
            self.__last_investment = amount
            self.capital -= amount
        else:
            print("current capital is less than " + amount)
        return self.capital

    def deposit_capital(self, amount: float) -> float:
        self.capital += amount
        return self.capital

    def acquire_equity(self, symbol: str, quantity: float) -> float:
        # if the target symbol already exist
        if symbol in self.equity:
            self.equity[symbol] += quantity
        else:
            self.equity[symbol] = quantity
        return self.equity[symbol]

    def forfeit_equity(self, symbol: str, quantity: float) -> float:
        '''
        forfeit part of specified equity
        '''
        # if the target symbol already exist
        if self.symbol in self.equity:
            self.equity[symbol] -= quantity
            # remove symbol if account hold none of it
            if self.equity[symbol] == 0:
                self.equity.pop(symbol)
        else:
            raise KeyError("no such equity")
        return quantity

    def forfeit_equity(self, symbol: str) -> float:
        '''
        forfeit all share of specified equity
        '''
        # if the target symbol already exist
        if symbol in self.equity:
            result = self.equity.pop(symbol)
        else:
            raise KeyError("no such equity")
        return result

    def revenue(self):
        '''
        calculate current revenue. Positive number is gain, negative number is loss.
        '''
        return self.get_current_capital() - self.__starting_capital

    def one_time_revenue(self):
        return self.get_current_capital() - self.__last_capital

    def win_rate():
        pass

    def max_win_and_max_loss():
        pass
