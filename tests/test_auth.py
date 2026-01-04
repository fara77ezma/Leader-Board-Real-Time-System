from controllers.auth import hash_password


class TestPasswordHashing:
    
    def test_hash_password_creates_hash(self):
        password = "MySecretPassword"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert hashed != password  
        assert len(hashed) > 20 