package semreg_thermal_map_contract

import (
	"encoding/json"
	"os"
	"testing"

	semreg "github.com/Project-Helianthus/helianthus-semreg/semreg/v1"
	"github.com/Project-Helianthus/helianthus-semreg/semreg/v1/packs/thermal"
)

// This validates the synthetic acceptance binding, not source qualification.
func TestDHWSetpointBindingAgainstThermalPack(t *testing.T) {
	data, err := os.ReadFile("../../architecture/fixtures/dhw-setpoint-semreg-cutover-v1.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		Keys  []semreg.FactKey `json:"keys"`
		Value semreg.Value     `json:"value"`
	}
	if err := json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	if len(fixture.Keys) != 2 {
		t.Fatal("expected two synthetic service keys")
	}
	for _, key := range fixture.Keys {
		if err := key.Validate(); err != nil {
			t.Fatalf("proposed key is structurally invalid: %v", err)
		}
		if err := thermal.New().ValidateFact(key, &fixture.Value); err == nil {
			t.Fatal("current pack unexpectedly accepts proposed service-aware key; review cutover contract")
		}
		// The supported single-dimension form validates the field and value,
		// but loses DHW service identity and must not be admitted as the proposal.
		key.Dimensions = key.Dimensions[1:]
		if err := thermal.New().ValidateFact(key, &fixture.Value); err != nil {
			t.Fatalf("supported temperature-only form fails Thermal pack: %v", err)
		}
		for _, number := range []struct {
			coefficient string
			exponent    int32
			valid       bool
		}{
			{"-5", 1, true}, {"0", 0, true}, {"15", 1, true},
			{"-51", 0, false}, {"16", 1, false},
		} {
			value := semreg.Value{Kind: semreg.ValueQuantity, Quantity: &semreg.Quantity{
				Number: semreg.Decimal{Coefficient: number.coefficient, Exponent10: number.exponent}, Unit: "unit.celsius",
			}}
			err := thermal.New().ValidateFact(key, &value)
			if (err == nil) != number.valid {
				t.Fatalf("pack representation range for %v: %v", number, err)
			}
		}
	}
}
