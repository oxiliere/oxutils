"""
Tests for OxUtils JWT module.
"""
import pytest
import jwt
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from oxutils.jwt.client import (
    fetch_jwks,
    get_jwks,
    get_public_key,
    verify_token,
    clear_jwks_cache,
)
from oxutils.jwt.auth import (
    get_jwks_from_file,
    get_public_key_from_file,
    clear_public_key_cache,
)
from oxutils.jwt.constants import JWT_ALGORITHM


class TestJWTConstants:
    """Test JWT constants."""
    
    def test_jwt_algorithm(self):
        """Test JWT algorithm constant."""
        assert JWT_ALGORITHM == 'RS256'


class TestJWKSFetching:
    """Test JWKS fetching from URL."""
    
    @patch('oxutils.jwt.client.requests.get')
    def test_fetch_jwks_success(self, mock_get):
        """Test successful JWKS fetching."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'keys': [
                {'kid': 'key1', 'kty': 'RSA', 'use': 'sig'}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        jwks = fetch_jwks('https://auth.example.com/.well-known/jwks.json')
        
        assert 'keys' in jwks
        assert len(jwks['keys']) == 1
        assert jwks['keys'][0]['kid'] == 'key1'
    
    @patch('oxutils.jwt.client.requests.get')
    def test_fetch_jwks_http_error(self, mock_get):
        """Test JWKS fetching with HTTP error."""
        mock_get.side_effect = Exception("Connection error")
        
        with pytest.raises(Exception):
            fetch_jwks('https://auth.example.com/.well-known/jwks.json')
    
    @patch('oxutils.jwt.client.fetch_jwks')
    def test_get_jwks_caching(self, mock_fetch):
        """Test JWKS caching."""
        mock_fetch.return_value = {'keys': [{'kid': 'key1'}]}
        
        # Clear cache first
        clear_jwks_cache()
        
        # First call should fetch
        jwks1 = get_jwks()
        assert mock_fetch.call_count == 1
        
        # Second call should use cache
        jwks2 = get_jwks()
        assert mock_fetch.call_count == 1
        assert jwks1 == jwks2
    
    def test_clear_jwks_cache(self):
        """Test clearing JWKS cache."""
        clear_jwks_cache()
        # Should not raise any errors


class TestPublicKeyRetrieval:
    """Test public key retrieval from JWKS."""
    
    @patch('oxutils.jwt.client.get_jwks')
    def test_get_public_key_success(self, mock_get_jwks):
        """Test successful public key retrieval."""
        mock_get_jwks.return_value = {
            'keys': [
                {
                    'kid': 'test-key-id',
                    'kty': 'RSA',
                    'use': 'sig',
                    'n': 'test-n',
                    'e': 'AQAB'
                }
            ]
        }
        
        with patch('oxutils.jwt.client.jwk.JWK.from_json') as mock_jwk:
            mock_key = Mock()
            mock_key.export_to_pem.return_value = b'-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----'
            mock_jwk.return_value = mock_key
            
            public_key = get_public_key('test-key-id')
            assert public_key is not None
    
    @patch('oxutils.jwt.client.get_jwks')
    def test_get_public_key_not_found(self, mock_get_jwks):
        """Test public key retrieval with non-existent kid."""
        mock_get_jwks.return_value = {
            'keys': [
                {'kid': 'other-key-id', 'kty': 'RSA'}
            ]
        }
        
        with pytest.raises(ValueError, match="Public key with kid"):
            get_public_key('test-key-id')


class TestTokenVerification:
    """Test JWT token verification."""
    
    def test_verify_token_success(self, temp_jwt_key, sample_jwt_payload):
        """Test successful token verification."""
        # Create a valid token
        token = jwt.encode(
            sample_jwt_payload,
            temp_jwt_key['private_key'],
            algorithm='RS256',
            headers={'kid': 'test-key-id'}
        )
        
        with patch('oxutils.jwt.client.get_public_key') as mock_get_key:
            mock_get_key.return_value = temp_jwt_key['public_key']
            
            payload = verify_token(token)
            
            assert payload['sub'] == 'user-123'
            assert payload['email'] == 'test@example.com'
    
    def test_verify_token_expired(self, temp_jwt_key):
        """Test token verification with expired token."""
        expired_payload = {
            'sub': 'user-123',
            'exp': datetime.utcnow() - timedelta(hours=1),
            'iat': datetime.utcnow() - timedelta(hours=2),
        }
        
        token = jwt.encode(
            expired_payload,
            temp_jwt_key['private_key'],
            algorithm='RS256',
            headers={'kid': 'test-key-id'}
        )
        
        with patch('oxutils.jwt.client.get_public_key') as mock_get_key:
            mock_get_key.return_value = temp_jwt_key['public_key']
            
            with pytest.raises(jwt.ExpiredSignatureError):
                verify_token(token)
    
    def test_verify_token_invalid_signature(self, temp_jwt_key, sample_jwt_payload):
        """Test token verification with invalid signature."""
        # Create token with one key
        token = jwt.encode(
            sample_jwt_payload,
            temp_jwt_key['private_key'],
            algorithm='RS256',
            headers={'kid': 'test-key-id'}
        )
        
        # Try to verify with different key
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
        
        different_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        ).public_key()
        
        with patch('oxutils.jwt.client.get_public_key') as mock_get_key:
            mock_get_key.return_value = different_key
            
            with pytest.raises(jwt.InvalidTokenError):
                verify_token(token)
    
    def test_verify_token_missing_kid(self, temp_jwt_key, sample_jwt_payload):
        """Test token verification with missing kid."""
        token = jwt.encode(
            sample_jwt_payload,
            temp_jwt_key['private_key'],
            algorithm='RS256',
            # No kid in headers
        )
        
        with pytest.raises(ValueError, match="Token header missing 'kid'"):
            verify_token(token)
    
    def test_verify_token_invalid_format(self):
        """Test token verification with invalid token format."""
        with pytest.raises(jwt.InvalidTokenError):
            verify_token("invalid.token.format")


class TestLocalKeyAuthentication:
    """Test local key file authentication."""
    
    def test_get_jwks_from_file(self, temp_jwt_key):
        """Test getting JWKS from local file."""
        with patch('oxutils.jwt.auth.oxi_settings') as mock_settings:
            mock_settings.jwt_verifying_key = temp_jwt_key['public_key_path']
            
            jwks = get_jwks_from_file()
            
            assert 'keys' in jwks
            assert len(jwks['keys']) == 1
    
    def test_get_public_key_from_file(self, temp_jwt_key):
        """Test getting public key from local file."""
        with patch('oxutils.jwt.auth.oxi_settings') as mock_settings:
            mock_settings.jwt_verifying_key = temp_jwt_key['public_key_path']
            
            public_key = get_public_key_from_file()
            
            assert public_key is not None
    
    def test_get_public_key_from_file_caching(self, temp_jwt_key):
        """Test public key caching."""
        with patch('oxutils.jwt.auth.oxi_settings') as mock_settings:
            mock_settings.jwt_verifying_key = temp_jwt_key['public_key_path']
            
            clear_public_key_cache()
            
            # First call
            key1 = get_public_key_from_file()
            
            # Second call should return cached key
            key2 = get_public_key_from_file()
            
            assert key1 == key2
    
    def test_clear_public_key_cache(self):
        """Test clearing public key cache."""
        clear_public_key_cache()
        # Should not raise any errors
    
    def test_get_public_key_from_file_not_configured(self):
        """Test getting public key when not configured."""
        with patch('oxutils.jwt.auth.oxi_settings') as mock_settings:
            mock_settings.jwt_verifying_key = None
            
            with pytest.raises(ValueError, match="JWT verifying key not configured"):
                get_public_key_from_file()


class TestJWTIntegration:
    """Test JWT integration scenarios."""
    
    def test_full_jwt_flow(self, temp_jwt_key):
        """Test complete JWT authentication flow."""
        # 1. Create token
        payload = {
            'sub': 'user-123',
            'email': 'test@example.com',
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
        }
        
        token = jwt.encode(
            payload,
            temp_jwt_key['private_key'],
            algorithm='RS256',
            headers={'kid': 'test-key-id'}
        )
        
        # 2. Verify token
        with patch('oxutils.jwt.client.get_public_key') as mock_get_key:
            mock_get_key.return_value = temp_jwt_key['public_key']
            
            verified_payload = verify_token(token)
            
            assert verified_payload['sub'] == payload['sub']
            assert verified_payload['email'] == payload['email']
