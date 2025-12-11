import unittest
import numpy as np
import physics

# Re-implementing the helper functions here to test the logic in isolation
# without triggering the matplotlib GUI window from main.py
def calculate_ik_logic(target_x, target_y):
    """
    The exact logic used in main.py for Inverse Kinematics.
    """
    # 1. Clamp target distance
    max_reach = physics.L1 + physics.L2 - 0.001
    dist_sq = target_x**2 + target_y**2
    dist = np.sqrt(dist_sq)
    
    if dist > max_reach:
        scale = max_reach / dist
        target_x *= scale
        target_y *= scale
        dist = max_reach

    # 2. Base angle
    base_angle = np.arctan2(target_x, -target_y)

    # 3. Internal angle alpha (Law of Cosines)
    cos_alpha = (physics.L1**2 + dist**2 - physics.L2**2) / (2 * physics.L1 * dist)
    cos_alpha = np.clip(cos_alpha, -1.0, 1.0)
    alpha = np.arccos(cos_alpha)

    # 4. Theta 1
    theta1 = base_angle - alpha

    # 5. Theta 2
    elbow_x = physics.L1 * np.sin(theta1)
    elbow_y = -physics.L1 * np.cos(theta1)
    
    dx = target_x - elbow_x
    dy = target_y - elbow_y
    
    theta2 = np.arctan2(dx, -dy)

    return theta1, theta2

def forward_kinematics(theta1, theta2):
    """
    Calculates (x, y) of the end effector given angles.
    Used to verify the result of IK.
    """
    x1 = physics.L1 * np.sin(theta1)
    y1 = -physics.L1 * np.cos(theta1)
    
    x2 = x1 + physics.L2 * np.sin(theta2)
    y2 = y1 - physics.L2 * np.cos(theta2)
    return x2, y2

class TestInverseKinematics(unittest.TestCase):
    
    def test_easy_reach(self):
        """Test a coordinate that is easily within reach."""
        # Target: Slightly to the right and down
        target_x, target_y = 1.0, -1.0
        
        t1, t2 = calculate_ik_logic(target_x, target_y)
        
        # Check if these angles put the bob at the target
        x_res, y_res = forward_kinematics(t1, t2)
        
        np.testing.assert_almost_equal(x_res, target_x, decimal=3)
        np.testing.assert_almost_equal(y_res, target_y, decimal=3)

    def test_out_of_bounds(self):
        """Test a coordinate that is impossible to reach (too far)."""
        # Target: Way too far to the right
        target_x, target_y = 10.0, -10.0
        
        t1, t2 = calculate_ik_logic(target_x, target_y)
        x_res, y_res = forward_kinematics(t1, t2)
        
        # The result should be at the max reach in the direction of the target
        max_reach = physics.L1 + physics.L2
        current_reach = np.hypot(x_res, y_res)
        
        # Allow small epsilon because logic uses -0.001 safety margin
        self.assertLess(current_reach, max_reach)
        self.assertGreater(current_reach, max_reach - 0.01)

    def test_vertical_hang(self):
        """Test dragging straight down."""
        target_x, target_y = 0.0, -1.9 # Within reach (L1+L2 = 2.0)
        
        t1, t2 = calculate_ik_logic(target_x, target_y)
        x_res, y_res = forward_kinematics(t1, t2)
        
        # Should be very close to 0 on x-axis
        np.testing.assert_almost_equal(x_res, 0.0, decimal=3)
        np.testing.assert_almost_equal(y_res, -1.9, decimal=3)

if __name__ == '__main__':
    unittest.main()