// backend/internal/util/password/password.go
package password

import "golang.org/x/crypto/bcrypt"

// Hash returns bcrypt hash for a plain password.
func Hash(plain string) (string, error) {
	b, err := bcrypt.GenerateFromPassword([]byte(plain), bcrypt.DefaultCost)
	return string(b), err
}

// Verify compares plain vs bcrypt hash.
func Verify(plain, hash string) error {
	return bcrypt.CompareHashAndPassword([]byte(hash), []byte(plain))
}
