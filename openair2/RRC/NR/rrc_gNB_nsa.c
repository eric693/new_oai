/*
 * Licensed to the OpenAirInterface (OAI) Software Alliance under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The OpenAirInterface Software Alliance licenses this file to You under
 * the OAI Public License, Version 1.1  (the "License"); you may not use this file
 * except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.openairinterface.org/?page_id=698
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *-------------------------------------------------------------------------------
 * For more information about the OpenAirInterface (OAI) Software Alliance:
 *      contact@openairinterface.org
 */

/*! \file rrc_gNB_nsa.c
 * \brief rrc NSA procedures for gNB
 * \author Raymond Knopp
 * \date 2019
 * \version 1.0
 * \company Eurecom
 * \email: raymond.knopp@eurecom.fr
 */
#ifndef RRC_GNB_NSA_C
#define RRC_GNB_NSA_C

#include "nr_rrc_defs.h"
#include "NR_RRCReconfiguration.h"
#include "NR_UE-NR-Capability.h"
//#include "NR_UE-CapabilityRAT-ContainerList.h"
#include "LTE_UE-CapabilityRAT-ContainerList.h"
#include "NR_CG-Config.h"
//#include "NR_SRB-ToAddModList.h"
#include "openair2/LAYER2/NR_MAC_gNB/mac_proto.h"
#include "openair2/RRC/LTE/rrc_eNB_GTPV1U.h"

extern boolean_t nr_rrc_pdcp_config_asn1_req(
    const protocol_ctxt_t *const  ctxt_pP,
    NR_SRB_ToAddModList_t  *const srb2add_list,
    NR_DRB_ToAddModList_t  *const drb2add_list,
    NR_DRB_ToReleaseList_t *const drb2release_list,
    const uint8_t                   security_modeP,
    uint8_t                  *const kRRCenc,
    uint8_t                  *const kRRCint,
    uint8_t                  *const kUPenc
  #if (LTE_RRC_VERSION >= MAKE_VERSION(9, 0, 0))
    ,LTE_PMCH_InfoList_r9_t  *pmch_InfoList_r9
  #endif
    ,rb_id_t                 *const defaultDRB,
    struct NR_CellGroupConfig__rlc_BearerToAddModList *rlc_bearer2add_list);

extern rlc_op_status_t nr_rrc_rlc_config_asn1_req (const protocol_ctxt_t   * const ctxt_pP,
    const NR_SRB_ToAddModList_t   * const srb2add_listP,
    const NR_DRB_ToAddModList_t   * const drb2add_listP,
    const NR_DRB_ToReleaseList_t  * const drb2release_listP,
    const LTE_PMCH_InfoList_r9_t * const pmch_InfoList_r9_pP,
    struct NR_CellGroupConfig__rlc_BearerToAddModList *rlc_bearer2add_list);

void rrc_parse_ue_capabilities(gNB_RRC_INST *rrc, LTE_UE_CapabilityRAT_ContainerList_t *UE_CapabilityRAT_ContainerList, x2ap_ENDC_sgnb_addition_req_t *m) {

  struct rrc_gNB_ue_context_s        *ue_context_p = NULL;
  OCTET_STRING_t *ueCapabilityRAT_Container_nr = NULL;
  OCTET_STRING_t *ueCapabilityRAT_Container_MRDC = NULL;
  int list_size;
  asn_dec_rval_t dec_rval;
  AssertFatal(UE_CapabilityRAT_ContainerList!=NULL,"UE_CapabilityRAT_ContainerList is null\n");
  AssertFatal((list_size=UE_CapabilityRAT_ContainerList->list.count) >= 2, "UE_CapabilityRAT_ContainerList->list.size %d < 2\n",UE_CapabilityRAT_ContainerList->list.count);
  for (int i=0;i<list_size;i++) {
    if (UE_CapabilityRAT_ContainerList->list.array[i]->rat_Type == LTE_RAT_Type_nr) ueCapabilityRAT_Container_nr = &UE_CapabilityRAT_ContainerList->list.array[i]->ueCapabilityRAT_Container;
    else if (UE_CapabilityRAT_ContainerList->list.array[i]->rat_Type == LTE_RAT_Type_eutra_nr) ueCapabilityRAT_Container_MRDC = &UE_CapabilityRAT_ContainerList->list.array[i]->ueCapabilityRAT_Container;
  }    

  // decode and store capabilities
  ue_context_p = rrc_gNB_allocate_new_UE_context(rrc);

  if (ueCapabilityRAT_Container_nr != NULL) {
    dec_rval = uper_decode(NULL,
                           &asn_DEF_NR_UE_NR_Capability,
                           (void **)&ue_context_p->ue_context.UE_Capability_nr,
                           ueCapabilityRAT_Container_nr->buf,
                           ueCapabilityRAT_Container_nr->size, 0, 0);

    if ((dec_rval.code != RC_OK) && (dec_rval.consumed == 0)) {
      LOG_E(RRC, "Failed to decode UE NR capabilities (%zu bytes) container size %lu\n", dec_rval.consumed,ueCapabilityRAT_Container_nr->size);
        ASN_STRUCT_FREE(asn_DEF_NR_UE_NR_Capability,
                        ue_context_p->ue_context.UE_Capability_nr);
        ue_context_p->ue_context.UE_Capability_nr = 0;
        AssertFatal(1==0,"exiting\n");
    }
  }

  if (ueCapabilityRAT_Container_MRDC != NULL) {
    dec_rval = uper_decode(NULL,
                           &asn_DEF_NR_UE_MRDC_Capability,
                           (void **)&ue_context_p->ue_context.UE_Capability_MRDC,
                           ueCapabilityRAT_Container_MRDC->buf,
                           ueCapabilityRAT_Container_MRDC->size, 0, 0);

    if ((dec_rval.code != RC_OK) && (dec_rval.consumed == 0)) {
        LOG_E(RRC, "Failed to decode UE MRDC capabilities (%zu bytes)\n", dec_rval.consumed);
        ASN_STRUCT_FREE(asn_DEF_NR_UE_MRDC_Capability,
                        ue_context_p->ue_context.UE_Capability_MRDC);
        ue_context_p->ue_context.UE_Capability_MRDC = 0;
        AssertFatal(1==0,"exiting\n");
    }
  }

  // dump ue_capabilities

  if ( LOG_DEBUGFLAG(DEBUG_ASN1 && ueCapabilityRAT_Container_nr != NULL) ) {
     xer_fprint(stdout, &asn_DEF_NR_UE_NR_Capability, ue_context_p->ue_context.UE_Capability_nr);
  }  

  if ( LOG_DEBUGFLAG(DEBUG_ASN1 && ueCapabilityRAT_Container_MRDC != NULL) ) {
     xer_fprint(stdout, &asn_DEF_NR_UE_MRDC_Capability, ue_context_p->ue_context.UE_Capability_MRDC);
  }  

  rrc_add_nsa_user(rrc,ue_context_p, m);
}

void rrc_add_nsa_user(gNB_RRC_INST *rrc,struct rrc_gNB_ue_context_s *ue_context_p, x2ap_ENDC_sgnb_addition_req_t *m) {

// generate nr-Config-r15 containers for LTE RRC : inside message for X2 EN-DC (CG-Config Message from 38.331)

  rrc_gNB_carrier_data_t *carrier=&rrc->carrier;

  MessageDef *msg;
  msg = itti_alloc_new_message(TASK_RRC_ENB, X2AP_ENDC_SGNB_ADDITION_REQ_ACK);
  gtpv1u_enb_create_tunnel_req_t  create_tunnel_req;
  gtpv1u_enb_create_tunnel_resp_t create_tunnel_resp;
  protocol_ctxt_t ctxt;

// NR RRCReconfiguration

  AssertFatal(rrc->Nb_ue < MAX_NR_RRC_UE_CONTEXTS,"cannot add another UE\n");

  ue_context_p->ue_context.reconfig = calloc(1,sizeof(NR_RRCReconfiguration_t));
  ue_context_p->ue_context.secondaryCellGroup = calloc(1,sizeof(NR_CellGroupConfig_t));
  memset((void*)ue_context_p->ue_context.reconfig,0,sizeof(NR_RRCReconfiguration_t));
  ue_context_p->ue_context.reconfig->rrc_TransactionIdentifier=0;
  ue_context_p->ue_context.reconfig->criticalExtensions.present = NR_RRCReconfiguration__criticalExtensions_PR_rrcReconfiguration;
  NR_RRCReconfiguration_IEs_t *reconfig_ies=calloc(1,sizeof(NR_RRCReconfiguration_IEs_t));
  ue_context_p->ue_context.reconfig->criticalExtensions.choice.rrcReconfiguration = reconfig_ies;
  carrier->initial_csi_index[rrc->Nb_ue] = 0;
  fill_default_reconfig(carrier->servingcellconfigcommon,
			reconfig_ies,
			ue_context_p->ue_context.secondaryCellGroup,
			carrier->pdsch_AntennaPorts,
			carrier->initial_csi_index[rrc->Nb_ue]);

  ue_context_p->ue_context.rb_config = calloc(1,sizeof(NR_RRCReconfiguration_t));
  //NR_CellGroupConfig_t               *secondaryCellGroup = ue_context_p->ue_context.secondaryCellGroup;
  //secondaryCellGroup->rlc_BearerToAddModList->list.array[0]->rlc_Config

  if(m!=NULL)
    fill_default_rbconfig(ue_context_p->ue_context.rb_config, m->e_rabs_tobeadded[0].e_rab_id, m->e_rabs_tobeadded[0].drb_ID);
  else
    fill_default_rbconfig(ue_context_p->ue_context.rb_config, 5, 1);
  ue_context_p->ue_id_rnti = ue_context_p->ue_context.secondaryCellGroup->spCellConfig->reconfigurationWithSync->newUE_Identity;
  NR_CG_Config_t *CG_Config = calloc(1,sizeof(*CG_Config));
  memset((void*)CG_Config,0,sizeof(*CG_Config));
  //int CG_Config_size = generate_CG_Config(rrc,CG_Config,ue_context_p->ue_context.reconfig,ue_context_p->ue_context.rb_config);
  generate_CG_Config(rrc,CG_Config,ue_context_p->ue_context.reconfig,ue_context_p->ue_context.rb_config);

  if(m!=NULL){
	  uint8_t inde_list[m->nb_e_rabs_tobeadded];
	  memset(inde_list, 0, m->nb_e_rabs_tobeadded*sizeof(uint8_t));

	  if (m->nb_e_rabs_tobeadded>0){
		  for (int i=0; i<m->nb_e_rabs_tobeadded; i++){
			  // Add the new E-RABs at the corresponding rrc ue context of the gNB
			  ue_context_p->ue_context.e_rab[i].param.e_rab_id = m->e_rabs_tobeadded[i].e_rab_id;
			  ue_context_p->ue_context.e_rab[i].param.gtp_teid = m->e_rabs_tobeadded[i].gtp_teid;
			  memcpy(&ue_context_p->ue_context.e_rab[i].param.sgw_addr, &m->e_rabs_tobeadded[i].sgw_addr, sizeof(transport_layer_addr_t));
			  ue_context_p->ue_context.nb_of_e_rabs++;
  			  //Fill the required E-RAB specific information for the creation of the S1-U tunnel between the gNB and the SGW
			  create_tunnel_req.eps_bearer_id[i]       = ue_context_p->ue_context.e_rab[i].param.e_rab_id;
			  create_tunnel_req.sgw_S1u_teid[i]        = ue_context_p->ue_context.e_rab[i].param.gtp_teid;
			  memcpy(&create_tunnel_req.sgw_addr[i], &ue_context_p->ue_context.e_rab[i].param.sgw_addr, sizeof(transport_layer_addr_t));
			  inde_list[i] = i;
                          LOG_I(RRC,"S1-U tunnel: index %d target sgw ip %d.%d.%d.%d length %d gtp teid %u\n",
			  		   	        	 i,
			  		      	        	create_tunnel_req.sgw_addr[i].buffer[0],
			  		      	            create_tunnel_req.sgw_addr[i].buffer[1],
			  		      	            create_tunnel_req.sgw_addr[i].buffer[2],
			  		      	            create_tunnel_req.sgw_addr[i].buffer[3],
			  		      	            create_tunnel_req.sgw_addr[i].length,
			  		      	            create_tunnel_req.sgw_S1u_teid[i]);   
		  }
		  //PM: Is this where we should extract the rnti from?
		  create_tunnel_req.rnti           = ue_context_p->ue_id_rnti;
		  create_tunnel_req.num_tunnels    = m->nb_e_rabs_tobeadded;
		  RB_INSERT(rrc_nr_ue_tree_s, &RC.nrrrc[rrc->module_id]->rrc_ue_head, ue_context_p);

		  PROTOCOL_CTXT_SET_BY_MODULE_ID(&ctxt, rrc->module_id, GNB_FLAG_YES, ue_context_p->ue_id_rnti, 0, 0,rrc->module_id);
		  gtpv1u_create_s1u_tunnel(
				  ctxt.instance,
				  &create_tunnel_req,
				  &create_tunnel_resp);
		  rrc_gNB_process_GTPV1U_CREATE_TUNNEL_RESP(
				  &ctxt,
				  &create_tunnel_resp,
				  &inde_list[0]);
		  X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).nb_e_rabs_admitted_tobeadded = m->nb_e_rabs_tobeadded;
		  for(int i=0; i<ue_context_p->ue_context.nb_of_e_rabs; i++){
			  X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).e_rabs_admitted_tobeadded[i].e_rab_id = ue_context_p->ue_context.e_rab[i].param.e_rab_id;
			  X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).e_rabs_admitted_tobeadded[i].gtp_teid = create_tunnel_resp.enb_S1u_teid[i];
			  memcpy(&X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).e_rabs_admitted_tobeadded[i].gnb_addr, &create_tunnel_resp.enb_addr, sizeof(transport_layer_addr_t));

			 //The length field in the X2AP targetting structure is expected in bits but the create_tunnel_resp returns the address length in bytes
		         X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).e_rabs_admitted_tobeadded[i].gnb_addr.length = create_tunnel_resp.enb_addr.length*8;

                          LOG_I(RRC,"S1-U create_tunnel_resp tunnel: index %d target gNB ip %d.%d.%d.%d length %d gtp teid %u\n",
					  i,
					  create_tunnel_resp.enb_addr.buffer[0],
					  create_tunnel_resp.enb_addr.buffer[1],
					  create_tunnel_resp.enb_addr.buffer[2],
					  create_tunnel_resp.enb_addr.buffer[3],
					  create_tunnel_resp.enb_addr.length,
					  create_tunnel_resp.enb_S1u_teid[i]);
			  LOG_I(RRC,"X2AP sGNB Addition Request: index %d target gNB ip %d.%d.%d.%d length %d gtp teid %u\n",
					  i,
					  X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).e_rabs_admitted_tobeadded[i].gnb_addr.buffer[0],
					  X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).e_rabs_admitted_tobeadded[i].gnb_addr.buffer[1],
					  X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).e_rabs_admitted_tobeadded[i].gnb_addr.buffer[2],
					  X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).e_rabs_admitted_tobeadded[i].gnb_addr.buffer[3],
					  X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).e_rabs_admitted_tobeadded[i].gnb_addr.length,
					  X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).e_rabs_admitted_tobeadded[i].gtp_teid);
		  }
	  }
	  else
		  LOG_W(RRC, "No E-RAB to be added received from SgNB Addition Request message \n");
  }


  //X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).rrc_buffer_size = CG_Config_size; //Need to verify correct value for the buffer_size
  // Send to X2 entity to transport to MeNB
  asn_enc_rval_t enc_rval = uper_encode_to_buffer(&asn_DEF_NR_CG_Config,
          	  	  	  	  	  	  	  	  	  	  NULL,
          	  	  	  	  	  	  	  	  	  	  (void *)CG_Config,
          	  	  	  	  	  	  	  	  	  	  X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).rrc_buffer,
												  1024);

  X2AP_ENDC_SGNB_ADDITION_REQ_ACK(msg).rrc_buffer_size = (enc_rval.encoded+7)>>3;

  itti_send_msg_to_task(TASK_X2AP, ENB_MODULE_ID_TO_INSTANCE(0), msg); //Check right id instead of hardcoding

  rrc->Nb_ue++;
  // configure MAC and RLC
  rrc_mac_config_req_gNB(rrc->module_id,
			 rrc->carrier.ssb_SubcarrierOffset,
                         rrc->carrier.pdsch_AntennaPorts,
			 NULL,
			 1, // add_ue flag
			 ue_context_p->ue_id_rnti,
			 ue_context_p->ue_context.secondaryCellGroup);

  nr_rrc_pdcp_config_asn1_req(
    &ctxt,
    (NR_SRB_ToAddModList_t *) NULL,
    ue_context_p->ue_context.rb_config->drb_ToAddModList ,
    ue_context_p->ue_context.rb_config->drb_ToReleaseList,
    0xff,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    ue_context_p->ue_context.secondaryCellGroup->rlc_BearerToAddModList);

  nr_rrc_rlc_config_asn1_req (&ctxt,
      (NR_SRB_ToAddModList_t *) NULL,
      ue_context_p->ue_context.rb_config->drb_ToAddModList,
      ue_context_p->ue_context.rb_config->drb_ToReleaseList,
      (LTE_PMCH_InfoList_r9_t *) NULL,
      ue_context_p->ue_context.secondaryCellGroup);

}


#endif
