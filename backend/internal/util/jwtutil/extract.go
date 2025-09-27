// backend/internal/util/jwtutil/extract.go
package jwtutil

import (
	"strings"
)

func ExtractBearerToken(authHeader string) string {
	if strings.HasPrefix(authHeader, "Bearer ") {
		return strings.TrimPrefix(authHeader, "Bearer ")
	}
	return ""
}
