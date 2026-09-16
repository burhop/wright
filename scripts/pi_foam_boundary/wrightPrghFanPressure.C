// Fixed registration of OpenFOAM's native fan law inside its native hydrostatic
// pressure adapter. No user-supplied code or alternate pressure law is evaluated.
#include "PrghPressureFvPatchScalarField.H"
#include "fanPressureFvPatchScalarField.H"

namespace Foam
{
    makePrghPatchScalarField(fanPressure, wrightPrghFanPressure)
}
