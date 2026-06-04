# -*- coding: utf-8 -*-
"""
债券定价模型模块
实现债券的定价、久期和凸性计算
"""
import numpy as np
from scipy.optimize import newton


class BondPricing:
    """债券定价类
    
    实现债券的定价、久期和凸性计算
    支持息票债券和零息债券
    """
    
    @staticmethod
    def price_coupon_bond(face_value, coupon_rate, years_to_maturity, yield_to_maturity, compounding_frequency=2):
        """计算息票债券的价格
        
        参数:
            face_value: 面值
            coupon_rate: 票面利率
            years_to_maturity: 到期时间（年）
            yield_to_maturity: 到期收益率
            compounding_frequency: 复利频率（默认2，即半年付息一次）
            
        返回:
            债券价格
        """
        # 计算每期利息
        coupon_payment = face_value * coupon_rate / compounding_frequency
        # 计算总期数
        total_periods = years_to_maturity * compounding_frequency
        # 计算每期贴现率
        periodic_yield = yield_to_maturity / compounding_frequency
        
        # 计算利息的现值
        if periodic_yield > 0:
            coupon_present_value = coupon_payment * (1 - (1 + periodic_yield) ** -total_periods) / periodic_yield
        else:
            coupon_present_value = coupon_payment * total_periods
        
        # 计算面值的现值
        face_present_value = face_value * (1 + periodic_yield) ** -total_periods
        
        # 债券价格 = 利息现值 + 面值现值
        bond_price = coupon_present_value + face_present_value
        
        return bond_price
    
    @staticmethod
    def price_zero_coupon_bond(face_value, years_to_maturity, yield_to_maturity, compounding_frequency=2):
        """计算零息债券的价格
        
        参数:
            face_value: 面值
            years_to_maturity: 到期时间（年）
            yield_to_maturity: 到期收益率
            compounding_frequency: 复利频率（默认2，即半年复利一次）
            
        返回:
            债券价格
        """
        # 计算总期数
        total_periods = years_to_maturity * compounding_frequency
        # 计算每期贴现率
        periodic_yield = yield_to_maturity / compounding_frequency
        
        # 零息债券价格 = 面值的现值
        bond_price = face_value * (1 + periodic_yield) ** -total_periods
        
        return bond_price
    
    @staticmethod
    def calculate_yield_to_maturity(face_value, coupon_rate, years_to_maturity, bond_price, compounding_frequency=2):
        """计算债券的到期收益率
        
        参数:
            face_value: 面值
            coupon_rate: 票面利率
            years_to_maturity: 到期时间（年）
            bond_price: 债券价格
            compounding_frequency: 复利频率（默认2，即半年付息一次）
            
        返回:
            到期收益率
        """
        # 定义目标函数：价格差异
        def price_difference(yield_to_maturity):
            calculated_price = BondPricing.price_coupon_bond(
                face_value, coupon_rate, years_to_maturity, yield_to_maturity, compounding_frequency
            )
            return calculated_price - bond_price
        
        # 使用牛顿法求解到期收益率
        # 初始猜测值设为票面利率
        initial_guess = coupon_rate
        
        try:
            ytm = newton(price_difference, initial_guess)
            return ytm
        except Exception as e:
            # 如果牛顿法失败，使用二分法
            # 定义搜索范围
            low = 0.001
            high = 1.0
            tolerance = 1e-6
            max_iterations = 100
            
            for _ in range(max_iterations):
                mid = (low + high) / 2
                mid_price = BondPricing.price_coupon_bond(
                    face_value, coupon_rate, years_to_maturity, mid, compounding_frequency
                )
                
                if abs(mid_price - bond_price) < tolerance:
                    return mid
                elif mid_price > bond_price:
                    high = mid
                else:
                    low = mid
            
            # 如果二分法也失败，返回最后一次的估计值
            return (low + high) / 2
    
    @staticmethod
    def calculate_macaulay_duration(face_value, coupon_rate, years_to_maturity, yield_to_maturity, compounding_frequency=2):
        """计算债券的麦考利久期
        
        参数:
            face_value: 面值
            coupon_rate: 票面利率
            years_to_maturity: 到期时间（年）
            yield_to_maturity: 到期收益率
            compounding_frequency: 复利频率（默认2，即半年付息一次）
            
        返回:
            麦考利久期
        """
        # 计算每期利息
        coupon_payment = face_value * coupon_rate / compounding_frequency
        # 计算总期数
        total_periods = years_to_maturity * compounding_frequency
        # 计算每期贴现率
        periodic_yield = yield_to_maturity / compounding_frequency
        # 计算债券价格
        bond_price = BondPricing.price_coupon_bond(
            face_value, coupon_rate, years_to_maturity, yield_to_maturity, compounding_frequency
        )
        
        # 计算麦考利久期
        macaulay_duration = 0
        for period in range(1, total_periods + 1):
            # 计算每期现金流
            if period == total_periods:
                cash_flow = coupon_payment + face_value
            else:
                cash_flow = coupon_payment
            # 计算现金流的现值
            present_value = cash_flow * (1 + periodic_yield) ** -period
            # 计算加权平均时间
            macaulay_duration += (period / compounding_frequency) * (present_value / bond_price)
        
        return macaulay_duration
    
    @staticmethod
    def calculate_modified_duration(face_value, coupon_rate, years_to_maturity, yield_to_maturity, compounding_frequency=2):
        """计算债券的修正久期
        
        参数:
            face_value: 面值
            coupon_rate: 票面利率
            years_to_maturity: 到期时间（年）
            yield_to_maturity: 到期收益率
            compounding_frequency: 复利频率（默认2，即半年付息一次）
            
        返回:
            修正久期
        """
        # 计算麦考利久期
        macaulay_duration = BondPricing.calculate_macaulay_duration(
            face_value, coupon_rate, years_to_maturity, yield_to_maturity, compounding_frequency
        )
        # 计算修正久期
        modified_duration = macaulay_duration / (1 + yield_to_maturity / compounding_frequency)
        
        return modified_duration
    
    @staticmethod
    def calculate_convexity(face_value, coupon_rate, years_to_maturity, yield_to_maturity, compounding_frequency=2):
        """计算债券的凸性
        
        参数:
            face_value: 面值
            coupon_rate: 票面利率
            years_to_maturity: 到期时间（年）
            yield_to_maturity: 到期收益率
            compounding_frequency: 复利频率（默认2，即半年付息一次）
            
        返回:
            凸性
        """
        # 计算每期利息
        coupon_payment = face_value * coupon_rate / compounding_frequency
        # 计算总期数
        total_periods = years_to_maturity * compounding_frequency
        # 计算每期贴现率
        periodic_yield = yield_to_maturity / compounding_frequency
        # 计算债券价格
        bond_price = BondPricing.price_coupon_bond(
            face_value, coupon_rate, years_to_maturity, yield_to_maturity, compounding_frequency
        )
        
        # 计算凸性
        convexity = 0
        for period in range(1, total_periods + 1):
            # 计算每期现金流
            if period == total_periods:
                cash_flow = coupon_payment + face_value
            else:
                cash_flow = coupon_payment
            # 计算现金流的现值
            present_value = cash_flow * (1 + periodic_yield) ** -period
            # 计算凸性贡献
            convexity_contribution = (period * (period + 1) / (compounding_frequency ** 2)) * present_value
            convexity += convexity_contribution
        
        # 标准化凸性
        convexity = convexity / (bond_price * (1 + periodic_yield) ** 2)
        
        return convexity
    
    @staticmethod
    def estimate_price_change(initial_price, modified_duration, convexity, yield_change):
        """使用久期和凸性估计收益率变化导致的债券价格变化
        
        参数:
            initial_price: 初始债券价格
            modified_duration: 修正久期
            convexity: 凸性
            yield_change: 收益率变化（小数形式）
            
        返回:
            估计的价格变化和新价格
        """
        # 价格变化百分比 = -修正久期 * 收益率变化 + 0.5 * 凸性 * (收益率变化)^2
        price_change_percent = -modified_duration * yield_change + 0.5 * convexity * (yield_change ** 2)
        # 价格变化金额
        price_change = initial_price * price_change_percent
        # 新价格
        new_price = initial_price + price_change
        
        return price_change, new_price
