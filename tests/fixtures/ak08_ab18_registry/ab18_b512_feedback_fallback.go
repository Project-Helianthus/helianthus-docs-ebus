package vaillant

import (
	_ "embed"
	ab18json "encoding/json"
	ab18fmt "fmt"
)

type Ab18Key struct {
	Ab18Family        string  `json:"family"`
	Ab18Variant       string  `json:"variant"`
	Ab18Primary       uint8   `json:"primary"`
	Ab18Secondary     *uint8  `json:"secondary"`
	Ab18Operation     *uint8  `json:"operation"`
	Ab18Direction     string  `json:"direction"`
	Ab18Field         string  `json:"field"`
	Ab18Alternative   string  `json:"alternative"`
	Ab18Group         *uint8  `json:"group"`
	Ab18InstanceScope string  `json:"instance_scope"`
	Ab18Register      *uint16 `json:"register"`
}

//go:embed data/ab18_b512_feedback_fallback.json
var ab18Data string

func ab18Validate(ab18Input []byte) (map[string]ab18json.RawMessage, error) {
	var ab18Rows []ab18json.RawMessage
	if ab18Error := ab18json.Unmarshal(ab18Input, &ab18Rows); ab18Error != nil {
		return nil, ab18Error
	}
	if ab18Rows == nil {
		return nil, ab18fmt.Errorf("ab18: expected JSON array")
	}
	ab18Index := make(map[string]ab18json.RawMessage, len(ab18Rows))
	for _, ab18Row := range ab18Rows {
		var ab18Envelope struct {
			Ab18ID       ab18json.RawMessage `json:"id"`
			Ab18Key      ab18json.RawMessage `json:"key"`
			Ab18Grade    ab18json.RawMessage `json:"grade"`
			Ab18RawForm  ab18json.RawMessage `json:"raw_form"`
			Ab18Feedback ab18json.RawMessage `json:"feedback"`
		}
		if ab18Error := ab18json.Unmarshal(ab18Row, &ab18Envelope); ab18Error != nil {
			return nil, ab18Error
		}
		for ab18Name, ab18Payload := range map[string]ab18json.RawMessage{"id": ab18Envelope.Ab18ID, "grade": ab18Envelope.Ab18Grade, "raw_form": ab18Envelope.Ab18RawForm, "feedback": ab18Envelope.Ab18Feedback} {
			if len(ab18Payload) == 0 || string(ab18Payload) == "null" || string(ab18Payload) == `""` {
				return nil, ab18fmt.Errorf("ab18: missing row field %s", ab18Name)
			}
		}
		var ab18Axes map[string]ab18json.RawMessage
		if ab18Error := ab18json.Unmarshal(ab18Envelope.Ab18Key, &ab18Axes); ab18Error != nil {
			return nil, ab18Error
		}
		for _, ab18Axis := range []string{"family", "variant", "primary", "secondary", "operation", "direction", "field", "alternative", "group", "instance_scope", "register"} {
			if _, ab18Present := ab18Axes[ab18Axis]; !ab18Present {
				return nil, ab18fmt.Errorf("ab18: missing identity axis %s", ab18Axis)
			}
		}
		if len(ab18Axes) != 11 {
			return nil, ab18fmt.Errorf("ab18: unexpected identity axes")
		}
		var ab18Key Ab18Key
		if ab18Error := ab18json.Unmarshal(ab18Envelope.Ab18Key, &ab18Key); ab18Error != nil {
			return nil, ab18Error
		}
		if ab18Key.Ab18Family == "" || ab18Key.Ab18Variant == "" || ab18Key.Ab18Direction == "" || ab18Key.Ab18Field == "" || ab18Key.Ab18Alternative == "" || ab18Key.Ab18InstanceScope == "" || string(ab18Axes["primary"]) == "null" {
			return nil, ab18fmt.Errorf("ab18: incomplete identity")
		}
		ab18Identity, ab18Error := ab18json.Marshal(ab18Key)
		if ab18Error != nil {
			return nil, ab18Error
		}
		if _, ab18Duplicate := ab18Index[string(ab18Identity)]; ab18Duplicate {
			return nil, ab18fmt.Errorf("ab18: duplicate identity")
		}
		ab18Index[string(ab18Identity)] = append(ab18json.RawMessage(nil), ab18Row...)
	}
	return ab18Index, nil
}

func Ab18Entries() (ab18json.RawMessage, error) {
	if _, ab18Error := ab18Validate([]byte(ab18Data)); ab18Error != nil {
		return nil, ab18Error
	}
	return append(ab18json.RawMessage(nil), ab18Data...), nil
}

func ab18Lookup(ab18Input []byte, ab18Key Ab18Key) (ab18json.RawMessage, bool, error) {
	ab18Index, ab18Error := ab18Validate(ab18Input)
	if ab18Error != nil {
		return nil, false, ab18Error
	}
	ab18Identity, ab18Error := ab18json.Marshal(ab18Key)
	if ab18Error != nil {
		return nil, false, ab18Error
	}
	ab18Row, ab18Found := ab18Index[string(ab18Identity)]
	return append(ab18json.RawMessage(nil), ab18Row...), ab18Found, nil
}

func Ab18Lookup(ab18Key Ab18Key) (ab18json.RawMessage, bool, error) {
	return ab18Lookup([]byte(ab18Data), ab18Key)
}
