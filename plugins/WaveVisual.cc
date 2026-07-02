#include <gz/msgs/param.pb.h>

#include <chrono>
#include <string>

#include <gz/common/Profiler.hh>
#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>

#include <gz/sim/Util.hh>

#include "asv_simulator/Wavefield.hh"
#include "asv_simulator/WaveVisual.hh"

using namespace asv;

/// \brief Private data class for WaveVisual plugin
struct WaveVisual::Implementation
{
  /// \brief Gazebo transport node
  public: gz::transport::Node node;

  /// \brief Publisher for wave parameters
  public: gz::transport::Node::Publisher waveParamsPub;

  /// \brief Name of the wave parameters topic
  public: std::string waveTopic = "/wavefield/parameters";

  /// \brief The wave parameters message
  public: gz::msgs::Param waveParamsMsg;

  /// \brief Wavefield parser and parameter generator.
  public: Wavefield wavefield;

  /// \brief Flag to indicate if wave parameters have been published
  public: bool waveParamsPublished = false;
};

//////////////////////////////////////////////////
WaveVisual::WaveVisual()
  : data(std::make_unique<Implementation>())
{
}

//////////////////////////////////////////////////
WaveVisual::~WaveVisual() = default;

//////////////////////////////////////////////////
void WaveVisual::Configure(const gz::sim::Entity &/*_entity*/,
                           const std::shared_ptr<const sdf::Element> &_sdf,
                           gz::sim::EntityComponentManager &/*_ecm*/,
                           gz::sim::EventManager &/*_eventMgr*/)
{
  if (!_sdf->HasElement("wavefield"))
  {
    gzerr << "No <wavefield> element found. The WaveVisual plugin will not be "
           << "loaded." << std::endl;
    return;
  }

  this->data->wavefield.Load(_sdf);
  this->data->waveTopic = this->data->wavefield.Topic();
  this->data->waveParamsMsg = this->data->wavefield.Parameters();

  // Publisher
  this->data->waveParamsPub =
      this->data->node.Advertise<gz::msgs::Param>(this->data->waveTopic);
  gzmsg << "Wave parameters will be published on [" << this->data->waveTopic
         << "]" << std::endl;
}

//////////////////////////////////////////////////
void WaveVisual::PostUpdate(const gz::sim::UpdateInfo &_info,
                            const gz::sim::EntityComponentManager &/*_ecm*/)
{
  // Publish parameters once after a short delay
  if (!this->data->waveParamsPublished && _info.simTime > std::chrono::seconds(1))
  {
    this->data->waveParamsPub.Publish(this->data->waveParamsMsg);
    this->data->waveParamsPublished = true;
  }
}

GZ_ADD_PLUGIN(asv::WaveVisual,
              gz::sim::System,
              WaveVisual::ISystemConfigure,
              WaveVisual::ISystemPostUpdate)

GZ_ADD_PLUGIN_ALIAS(asv::WaveVisual, "asv::WaveVisual")
