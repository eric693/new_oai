/*******************************************************************************
    OpenAirInterface
    Copyright(c) 1999 - 2014 Eurecom

    OpenAirInterface is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.


    OpenAirInterface is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OpenAirInterface.The full GNU General Public License is
   included in this distribution in the file called "COPYING". If not,
   see <http://www.gnu.org/licenses/>.

  Contact Information
  OpenAirInterface Admin: openair_admin@eurecom.fr
  OpenAirInterface Tech : openair_tech@eurecom.fr
  OpenAirInterface Dev  : openair4g-devel@eurecom.fr

  Address      : Eurecom, Compus SophiaTech 450, route des chappes, 06451 Biot, France.

 *******************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#include "OctetString.h"

#ifndef VOICE_DOMAIN_PREFERENCE_AND_UE_USAGE_SETTING_H_
#define VOICE_DOMAIN_PREFERENCE_AND_UE_USAGE_SETTING_H_

#define VOICE_DOMAIN_PREFERENCE_AND_UE_USAGE_SETTING_MINIMUM_LENGTH 1
#define VOICE_DOMAIN_PREFERENCE_AND_UE_USAGE_SETTING_MAXIMUM_LENGTH 1

typedef struct VoiceDomainPreferenceAndUeUsageSetting_tag {
  uint8_t  spare:5;
#define UE_USAGE_SETTING_VOICE_CENTRIC 0b0
#define UE_USAGE_SETTING_DATA_CENTRIC  0b1
  uint8_t  ue_usage_setting:1;
#define VOICE_DOMAIN_PREFERENCE_CS_VOICE_ONLY                                    0b00
#define VOICE_DOMAIN_PREFERENCE_IMS_PS_VOICE_ONLY                                0b01
#define VOICE_DOMAIN_PREFERENCE_CS_VOICE_PREFERRED_IMS_PS_VOICE_AS_SECONDARY     0b10
#define VOICE_DOMAIN_PREFERENCE_IMS_PS_VOICE_PREFERRED_CS_VOICE_AS_SECONDARY     0b11
  uint8_t  voice_domain_for_eutran:2;
} VoiceDomainPreferenceAndUeUsageSetting;

int encode_voice_domain_preference_and_ue_usage_setting(VoiceDomainPreferenceAndUeUsageSetting *voicedomainpreferenceandueusagesetting, uint8_t iei, uint8_t *buffer, uint32_t len);

int decode_voice_domain_preference_and_ue_usage_setting(VoiceDomainPreferenceAndUeUsageSetting *voicedomainpreferenceandueusagesetting, uint8_t iei, uint8_t *buffer, uint32_t len);

void dump_voice_domain_preference_and_ue_usage_setting_xml(VoiceDomainPreferenceAndUeUsageSetting *voicedomainpreferenceandueusagesetting, uint8_t iei);

#endif /* VOICE DOMAIN PREFERENCE AND UE USAGE SETTING_H_ */
